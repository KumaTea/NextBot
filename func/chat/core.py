import random
import asyncio
import logging
from time import time
from bot.tools import get_dialog, retry_on_flood
from bot.session import msg_store
from typing import AsyncGenerator
from share.common import no_preview
from gpt.data import thinking_emojis
from telethon.tl.custom import Message
from telethon.errors import MessageNotModifiedError
from telethon import TelegramClient as Client
from gpt.core import stream_chat_by_sentences
from common.info import max_chunk, gpt_model, reasoning_model, min_edit_interval
from gpt.tools import gen_thread, gpt_to_bot, get_cmd_type, trim_starting_username


# The model asks for a message break with this token.
separator = '|SEP|'

# Telegram refuses anything over 4096 characters. Cut earlier than that: the
# raw text still has to survive `format_think`, which adds fences.
overflow_at = 3800

# Where to prefer breaking an over-long reply, best first.
split_seps = ('\n\n', '\n', '。', '. ')

# A provider error can run to thousands of characters, and an error message
# that is itself too long to send fails a second time.
error_limit = 300

# Telegram takes at most 100 message ids in one `get_messages` call.
max_fetch_ids = 100


@retry_on_flood(1)
async def _edit(message: Message, text: str) -> Message:
    return await message.edit(text, **no_preview)


@retry_on_flood(1)
async def _reply(message: Message, text: str) -> Message:
    return await message.reply(text, **no_preview)


def format_think(text: str) -> str:
    """Turn a <think> block into a fenced code block."""
    if '<think>' not in text:
        return text
    text = text.replace('<think>', '```think')
    if '</think>' not in text:
        return text + '```'
    return text.replace('</think>', '```')


def render(raw: str) -> str:
    """The display form of what the model has produced so far."""
    return format_think(gpt_to_bot(trim_starting_username(raw.strip())))


def brief(error: Exception) -> str:
    text = str(error).replace('\n', ' ').strip()
    return f'{text[:error_limit]}…' if len(text) > error_limit else text


def split_point(raw: str) -> int:
    """Where to break an over-long reply, preferring a natural boundary."""
    window = raw[:overflow_at]
    for sep in split_seps:
        index = window.rfind(sep)
        # only worth it if the break is not right at the start
        if index > overflow_at // 2:
            return index + len(sep)
    return overflow_at


async def type_in_message(
        message: Message,
        generator: AsyncGenerator[str, None],
        dialog: list[Message] = None
) -> Message:
    """
    Stream a reply into Telegram, editing the message as the text arrives.

    Only the text actually on screen is tracked, so an edit is never sent for
    something already displayed -- Telegram rejects those, and the old
    last-25-characters comparison could not tell the difference.
    """
    # `current` is the message being typed into; None means the next piece of
    # text needs a message of its own.
    current = message
    anchor = message
    shown = message.raw_text or ''
    text = ''
    chunk_len = 0
    last_edit = 0.0  # 0 => the first flush goes out without waiting

    async def show(body: str):
        nonlocal current, anchor, shown
        if not body:
            return
        if current is None:
            # created with its content, so it is never sent and then
            # immediately edited to the same thing
            current = await _reply(anchor, body)
            anchor = current
            shown = body
            msg_store.add(current)
            return
        if body == shown:
            return
        try:
            current = await _edit(current, body)
        except MessageNotModifiedError:
            pass
        shown = body

    def start_new_message(remainder: str):
        nonlocal current, shown, chunk_len, last_edit
        current, shown = None, ''
        chunk_len = len(remainder)
        last_edit = 0.0

    async for chunk in generator:
        text += chunk
        chunk_len += len(chunk)

        # an explicit break asked for by the model
        while separator in text:
            head, text = text.split(separator, 1)
            body = render(head)
            if not body:
                # nothing before the separator -- drop it and carry on
                continue
            await show(body)
            start_new_message(text)

        # a reply longer than Telegram will accept
        while len(text) > overflow_at:
            cut = split_point(text)
            head, text = text[:cut], text[cut:]
            await show(render(head))
            start_new_message(text)

        if chunk_len > max_chunk and time() - last_edit >= min_edit_interval:
            # rendering is only worth doing when it is about to be displayed
            await show(render(text))
            chunk_len = 0
            last_edit = time()

    await show(render(text))
    if current is not None:
        msg_store.add(current)
    return current or anchor


def no_input(message: Message) -> bool:
    command = message.raw_text or ''
    if command.find(' ') == -1:
        # no text
        return not message.reply_to_msg_id
    return False


async def chat_core(client: Client, message: Message, query_dialog: bool = True, resp_text: str = '') -> Message:
    if not resp_text:
        resp_text = random.choice(thinking_emojis) + '❓'
    resp_message = await message.reply(resp_text)

    # Held across generation, not just the lookup: the indicator used to stop
    # the moment the dialog was fetched, which is when the wait actually starts.
    async with client.action(message.chat_id, 'typing'):
        if query_dialog:
            dialog = await get_dialog(client, message)
        else:
            dialog = [message]
        thread = gen_thread(dialog)

        model = gpt_model
        first_msg_text = dialog[0].raw_text
        if first_msg_text:
            if get_cmd_type(first_msg_text) == 'smart':
                model = reasoning_model

        try:
            return await type_in_message(
                resp_message, stream_chat_by_sentences(thread, model=model), dialog
            )
        except Exception as e:
            logging.exception('[func_chat]\tGeneration failed')
            try:
                return await _edit(resp_message, f'发生错误: {brief(e)}')
            except Exception:
                logging.exception('[func_chat]\tCould not report the error either')
                return resp_message


async def get_last_n_messages(client: Client, message: Message, n: int) -> list[Message]:
    """
    The n messages before this one.

    Bots may not call `getHistory` -- Telegram answers `BotMethodInvalidError`
    -- so `limit=`/`max_id=` are not available here and messages have to be
    fetched by id. Ids are not contiguous, though (deletions and service
    messages consume them), so ask over a wider window and keep whatever of it
    actually exists.
    """
    window = min(max(n * 2, n + 10), max_fetch_ids)
    first = max(1, message.id - window)
    ids = list(range(first, message.id))
    if not ids:
        return []

    messages = await client.get_messages(message.chat_id, ids=ids)
    # ids were requested in ascending order, so this is already chronological
    return [m for m in messages if m][-n:]


def format_last_n_messages(this_message: Message, last_n_messages: list[Message]) -> Message:
    last_n_messages_text = '\n'.join(m.raw_text.strip() for m in last_n_messages if m.raw_text)
    this_message_command = this_message.raw_text.split(' ')[0]
    # set the raw text directly; the old entities no longer line up
    this_message.message = f'{this_message_command} {last_n_messages_text}'
    this_message.entities = None
    return this_message
