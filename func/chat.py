import random
import asyncio
from time import time
from pyrogram import Client
from bot.tools import get_dialog
from bot.auth import ensure_not_bl
from gpt.auth import ensure_gpt_auth
from typing import Union, AsyncGenerator
from cmn.session import gpt_auth, msg_store
from gpt.core import stream_chat_by_sentences
from pyrogram.enums.parse_mode import ParseMode
from cmn.data import smart_inst, thinking_emojis
from pyrogram.types import Message, CallbackQuery
from cmn.info import gpt_admins, max_chunk, min_edit_interval
from gpt.tools import gen_thread, gpt_to_bot, trim_starting_username


async def type_in_message(message: Message, generator: AsyncGenerator[str, None]) -> Message:
    text = ''
    msg = message
    parse_mode = None
    chunk_len = 0
    last_edit = time()
    async for chunk in generator:
        chunk = gpt_to_bot(trim_starting_username(chunk))
        text += chunk
        chunk_len += len(chunk)
        if '`' in text:
            parse_mode = ParseMode.MARKDOWN
        if text.lower().startswith('@chatgpt: '):
            text = text[len('@chatgpt: '):]
        if chunk_len > max_chunk and time() - last_edit > min_edit_interval:
            msg = await msg.edit_text(text, parse_mode=parse_mode, disable_web_page_preview=True)
            chunk_len = 0
            last_edit = time()
    # last words
    if msg.text.strip().lower()[-max_chunk:] != text.strip().lower()[-max_chunk:]:
        await asyncio.sleep(max(0, min_edit_interval - (time() - last_edit)))
        msg = await msg.edit_text(text, parse_mode=parse_mode, disable_web_page_preview=True)
    msg_store.add(msg)
    return msg


async def callback_gpt_auth(client: Client, callback_query: CallbackQuery) -> tuple:
    task, subtask, user_id, confirm = callback_query.data.split('_')
    user_id = int(user_id)
    message = callback_query.message
    async_tasks = []
    if callback_query.from_user.id in gpt_admins:
        if confirm == 'y':
            gpt_auth.add_user(user_id)
            async_tasks.append(message.edit_text('现在我可以和你聊天啦！'))
            async_tasks.append(callback_query.answer('已授权'))  # for admin
        else:
            async_tasks.append(message.edit_text('我还不能跟你聊天捏。'))
            async_tasks.append(callback_query.answer('已拒绝'))
    else:
        async_tasks.append(callback_query.answer('不是你的别乱按！', show_alert=True))
    return await asyncio.gather(*async_tasks)


async def gpt_callback_handler(client, callback_query):
    subtask = callback_query.data.split('_')[1]

    if subtask == 'auth':
        return await callback_gpt_auth(client, callback_query)


@ensure_not_bl
@ensure_gpt_auth
async def command_chat(client: Client, message: Message) -> Union[Message, None]:
    command = message.text
    content_index = command.find(' ')
    reply = message.reply_to_message
    if content_index == -1:
        # no text
        if not reply:
            return await message.reply_text('/chat 不支持无输入调用。')

    dialog, resp_message = await asyncio.gather(
        get_dialog(client, message),
        message.reply_text(random.choice(thinking_emojis) + '❓')
    )

    thread = gen_thread(dialog)
    return await type_in_message(resp_message, stream_chat_by_sentences(thread))


@ensure_not_bl
@ensure_gpt_auth
async def command_smart(client: Client, message: Message) -> Union[Message, None]:
    command = message.text
    content_index = command.find(' ')
    if content_index == -1:
        # no text
        return await message.reply_text('/smart 不支持无输入调用。')

    resp_message = await message.reply_text(random.choice(thinking_emojis) + '❓')
    thread = gen_thread([message], custom_inst=smart_inst)
    return await type_in_message(resp_message, stream_chat_by_sentences(thread))


@ensure_not_bl
@ensure_gpt_auth
async def command_debate(client: Client, message: Message) -> Union[Message, None]:
    command = message.text
    content_index = command.find(' ')
    if content_index == -1:
        # no text
        return await message.reply_text('/debate 不支持无输入调用。')

    dialog, resp_message = await asyncio.gather(
        get_dialog(client, message),
        message.reply_text(random.choice(thinking_emojis) + '❓')
    )
    thread = gen_thread(dialog)
    return await type_in_message(resp_message, stream_chat_by_sentences(thread))
