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
from pyrogram.enums.parse_mode import ParseMode
from pyrogram.enums.chat_action import ChatAction
from common.info import max_chunk, min_edit_interval, gpt_model, reasoning_model
from gpt.tools import gen_thread, gpt_to_bot, trim_starting_username, get_cmd_type


async def type_in_message(
        message: Message,
        generator: AsyncGenerator[str, None],
        dialog: list[Message] = None
) -> Message:
    text = ''
    parse_mode = None
    chunk_len = 0
    last_edit = time()
    is_search = False
    async for chunk in generator:
        chunk = gpt_to_bot(trim_starting_username(chunk))
        text += chunk
        chunk_len += len(chunk)
        if '`' in text:
            parse_mode = ParseMode.MARKDOWN
        if text.lower().startswith('@deepseek: '):
            text = text[len('@deepseek: '):]
        if text.lower().startswith('/search'):
            is_search = True
        if not is_search and chunk_len > max_chunk and time() - last_edit > min_edit_interval:
            message = await message.edit_text(text, parse_mode=parse_mode, disable_web_page_preview=True)
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
    if not is_search and message.text.strip().lower()[-max_chunk:] != text.strip().lower()[-max_chunk:]:
        await asyncio.sleep(max(0, min_edit_interval - (time() - last_edit)))
        message = await message.edit_text(text, parse_mode=parse_mode, disable_web_page_preview=True)
    msg_store.add(message)
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


async def chat_core(client: Client, message: Message, query_dialog: bool = True) -> Message:
    resp_message = await message.reply_text(random.choice(thinking_emojis) + '❓')

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
