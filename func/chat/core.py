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
from common.data import thinking_emojis
from gpt.core import stream_chat_by_sentences
from pyrogram.enums.parse_mode import ParseMode
from pyrogram.enums.chat_action import ChatAction
from common.info import max_chunk, min_edit_interval
from gpt.tools import gen_thread, gpt_to_bot, trim_starting_username


async def type_in_message(
        message: Message,
        generator: AsyncGenerator[str, None],
        dialog: list[Message] = None
) -> Message:
    text = ''
    msg = message
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
        if text.lower().startswith('@chatgpt: '):
            text = text[len('@chatgpt: '):]
        if text.lower().startswith('/search'):
            is_search = True
        if not is_search and chunk_len > max_chunk and time() - last_edit > min_edit_interval:
            msg = await msg.edit_text(text, parse_mode=parse_mode, disable_web_page_preview=True)
            chunk_len = 0
            last_edit = time()
    if is_search:
        logging.info(f'GPT has requested: {text}')
        search_result = await get_search_result(text)
        return await re_ask_with_search_result(message, search_result, dialog)
    # last words
    if not is_search and msg.text.strip().lower()[-max_chunk:] != text.strip().lower()[-max_chunk:]:
        await asyncio.sleep(max(0, min_edit_interval - (time() - last_edit)))
        msg = await msg.edit_text(text, parse_mode=parse_mode, disable_web_page_preview=True)
    msg_store.add(msg)
    return msg


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


async def chat_core(client: Client, message: Message) -> Message:
    resp_message = await message.reply_text(random.choice(thinking_emojis) + '❓')

    dialog, _ = await asyncio.gather(
        get_dialog(client, message),
        message.reply_chat_action(ChatAction.TYPING)
    )

    thread = gen_thread(dialog)
    return await type_in_message(resp_message, stream_chat_by_sentences(thread), dialog)
