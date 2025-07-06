import random
import asyncio
from time import time
from pyrogram import Client
from search.main import search
from bot.session import logging
from bot.tools import get_dialog
from bot.session import msg_store
from typing import AsyncGenerator
from pyrogram.types import Message
from gpt.data import thinking_emojis
from gpt.core import stream_chat_by_sentences
# from pyrogram.enums.parse_mode import ParseMode
from pyrogram.enums.chat_action import ChatAction
from common.info import max_chunk, min_edit_interval, gpt_model, reasoning_model
from gpt.tools import gen_thread, gpt_to_bot, trim_starting_username, get_cmd_type, trim_command


async def type_in_message(
        message: Message,
        generator: AsyncGenerator[str, None],
        dialog: list[Message] = None
) -> Message:
    text = ''
    edited_text = ''
    chunk_len = 0
    last_edit = time()
    is_search = False
    async for chunk in generator:
        # chunk = gpt_to_bot(trim_starting_username(chunk))
        # chunk may not present a full username, so we need to trim the whole text
        text += chunk
        chunk_len += len(chunk)
        # if '`' in text:
        #     parse_mode = ParseMode.MARKDOWN
        if text.lower().startswith('/search'):
            is_search = True
        # edited_text = text
        # edited_text = gpt_to_bot(trim_starting_username(edited_text))
        edited_text = gpt_to_bot(trim_starting_username(text.strip()))
        # think
        if '<think>' in text:
            edited_text = edited_text.replace('<think>', '```think')
            if '</think>' not in edited_text:
                edited_text += '```'
            else:
                edited_text = edited_text.replace('</think>', '```')
        if not is_search and chunk_len > max_chunk and time() - last_edit > min_edit_interval:
            message = await message.edit_text(edited_text, disable_web_page_preview=True)
            chunk_len = 0
            last_edit = time()
    if is_search:
        logging.info(f'GPT has requested: {text}')
        # search_result = await get_search_result(text)
        search_result, message = await asyncio.gather(
            get_search_result(text),
            message.edit_text('进行一个索的搜……')
        )
        return await re_ask_with_search_result(message, search_result, dialog)
    # last words
    if not is_search and message.text.strip().lower()[-max_chunk:] != edited_text.strip().lower()[-max_chunk:]:
        await asyncio.sleep(max(0, min_edit_interval - (time() - last_edit)))
        message = await message.edit_text(edited_text, disable_web_page_preview=True)
    msg_store.add(message)
    msg_store.save()
    return message


async def re_ask_with_search_result(
        message: Message,
        search_result: str,
        dialog: list[Message]
) -> Message:
    thread = gen_thread(dialog, search_result=search_result)
    return await type_in_message(message, stream_chat_by_sentences(thread), dialog)


async def get_search_result(text: str) -> str:
    # text.lower().startswith('/search')
    query = text[len('/search'):].strip()
    return await search(query)


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

    return await type_in_message(resp_message, stream_chat_by_sentences(thread, model=model), dialog)


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
