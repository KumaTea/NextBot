import random
import asyncio
from time import time
from pyrogram import Client
from bot.tools import get_dialog
from bot.session import msg_store
from typing import AsyncGenerator
from pyrogram.types import Message
from share.common import no_preview
from gpt.data import thinking_emojis
from gpt.core import stream_chat_by_sentences
from pyrogram.enums.chat_action import ChatAction
from common.info import max_chunk, gpt_model, reasoning_model, min_edit_interval
from gpt.tools import gen_thread, gpt_to_bot, get_cmd_type, trim_starting_username


async def type_in_message(
        message: Message,
        generator: AsyncGenerator[str, None],
        dialog: list[Message] = None
) -> Message:
    text = ''
    edited_text = ''
    chunk_len = 0
    last_edit = time()
    async for chunk in generator:
        text += chunk
        chunk_len += len(chunk)

        # Check for |SEP| token to split into multiple messages
        if '|SEP|' in text:
            sep_index = text.index('|SEP|')
            current_text = text[:sep_index]
            remaining_text = text[sep_index + len('|SEP|'):]

            # Finalize current message with content before |SEP|
            edited_text = gpt_to_bot(trim_starting_username(current_text.strip()))
            # Apply think tag formatting
            if '<think>' in current_text:
                edited_text = edited_text.replace('<think>', '```think')
                if '</think>' not in edited_text:
                    edited_text += '```'
                else:
                    edited_text = edited_text.replace('</think>', '```')

            await asyncio.sleep(max(0, min_edit_interval - (time() - last_edit)))
            message = await message.edit_text(edited_text, **no_preview)
            msg_store.add(message)
            msg_store.save()

            # Create a new message with remaining content
            new_message = await message.reply_text(remaining_text)

            # Create a generator that yields the remaining text
            async def remaining_generator():
                yield remaining_text
                async for _chunk in generator:
                    yield _chunk

            # Recursively call type_in_message with remaining content
            return await type_in_message(new_message, remaining_generator(), dialog)

        edited_text = gpt_to_bot(trim_starting_username(text.strip()))
        # think
        if '<think>' in text:
            edited_text = edited_text.replace('<think>', '```think')
            if '</think>' not in edited_text:
                edited_text += '```'
            else:
                edited_text = edited_text.replace('</think>', '```')
        if chunk_len > max_chunk and time() - last_edit > min_edit_interval:
            message = await message.edit_text(edited_text, **no_preview)
            chunk_len = 0
            last_edit = time()

    # last words
    if message.text.strip().lower()[-max_chunk:] != edited_text.strip().lower()[-max_chunk:]:
        await asyncio.sleep(max(0, min_edit_interval - (time() - last_edit)))
        message = await message.edit_text(edited_text, **no_preview)
    msg_store.add(message)
    msg_store.save()
    return message



def no_input(message: Message) -> bool:
    command = message.text
    content_index = command.find(' ')
    reply = message.reply_to_message
    if content_index == -1:
        # no text
        if not reply:
            return True
    return False


async def chat_core(client: Client, message: Message, query_dialog: bool = True, resp_text: str = '') -> Message:
    if not resp_text:
        resp_text = random.choice(thinking_emojis) + '❓'
    resp_message = await message.reply_text(resp_text)

    if query_dialog:
        dialog, _ = await asyncio.gather(
            get_dialog(client, message),
            message.reply_chat_action(ChatAction.TYPING)
        )
        thread = gen_thread(dialog)
    else:
        await message.reply_chat_action(ChatAction.TYPING)
        dialog = [message]
        thread = gen_thread([message])

    model = gpt_model
    first_msg_text = dialog[0].text
    if first_msg_text:
        command = get_cmd_type(first_msg_text)
        if command == 'smart':
            model = reasoning_model

    try:
        return await type_in_message(resp_message, stream_chat_by_sentences(thread, model=model), dialog)
    except Exception as e:
        return await resp_message.edit_text(f'发生错误: {e}')


async def get_last_n_messages(client: Client, message: Message, n: int) -> list[Message]:
    this_msg_id = message.id
    to_get_ids = [i for i in range(this_msg_id - n, this_msg_id)]

    messages = await client.get_messages(message.chat.id, to_get_ids)
    return messages


def format_last_n_messages(this_message: Message, last_n_messages: list[Message]) -> Message:
    last_n_messages_text = '\n'.join([m.text.strip() for m in last_n_messages if m.text.strip()])
    this_message_command = this_message.text.split(' ')[0]
    this_message.text = f'{this_message_command} {last_n_messages_text}'
    return this_message
