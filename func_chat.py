import asyncio
from time import time
from pyrogram import Client
from session import gpt_auth
from tg_tools import get_dialog
from typing import Union, AsyncGenerator
from bot_db import gpt_auth_info, smart_inst
from gpt_core import stream_chat_by_sentences
from bot_auth import ensure_not_bl, multi_dec
from pyrogram.enums.parse_mode import ParseMode
from bot_info import gpt_admins, max_chunk, min_edit_interval
from gpt_tools import gen_thread, gpt_to_bot, trim_starting_username
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery


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
            msg = await msg.edit_text(text, parse_mode=parse_mode)
            chunk_len = 0
            last_edit = time()
    # last words
    if msg.text.strip().lower()[-max_chunk:] != text.strip().lower()[-max_chunk:]:
        await asyncio.sleep(max(0, min_edit_interval - (time() - last_edit)))
        msg = await msg.edit_text(text, parse_mode=parse_mode)
    return msg


def has_gpt_auth(client: Client, message: Message) -> bool:
    if message.from_user:
        user_id = message.from_user.id
        if user_id in gpt_auth.users:
            return True
    return False


async def ask_for_gpt_auth(client: Client, message: Message) -> Union[Message, None]:
    user_id = message.from_user.id
    reply_markup = InlineKeyboardMarkup([
        [InlineKeyboardButton('允许', callback_data=f'gpt_auth_{user_id}_y')],
        [InlineKeyboardButton('拒绝', callback_data=f'gpt_auth_{user_id}_n')]
    ])
    return await message.reply_text(gpt_auth_info, reply_markup=reply_markup)


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


def ensure_gpt_auth(func):
    async def wrapper(client: Client, message: Message):
        if has_gpt_auth(client, message):
            return await func(client, message)
        else:
            return await ask_for_gpt_auth(client, message)
    return wrapper


@multi_dec([ensure_not_bl, ensure_gpt_auth])
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
        message.reply_text('...')
    )

    thread = gen_thread(dialog)
    return await type_in_message(resp_message, stream_chat_by_sentences(thread))


@multi_dec([ensure_not_bl, ensure_gpt_auth])
async def command_smart(client: Client, message: Message) -> Union[Message, None]:
    command = message.text
    content_index = command.find(' ')
    if content_index == -1:
        # no text
        return await message.reply_text('/smart 不支持无输入调用。')

    resp_message = await message.reply_text('...')
    thread = gen_thread([message], custom_inst=smart_inst)
    return await type_in_message(resp_message, stream_chat_by_sentences(thread))
