import asyncio
from pyrogram import Client
from typing import Optional
from gpt.auth import gpt_auth
from bot.session import msg_store
from bot.auth import ensure_not_bl
from common.info import gpt_admins
from gpt.auth import ensure_gpt_auth
from func.chat.core import chat_core, no_input
from pyrogram.types import Message, CallbackQuery


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
async def command_chat(client: Client, message: Message) -> Optional[Message]:
    if no_input(message):
        command = message.text
        command_handle = command.split(' ')[0].split('@')[0].lower()
        return await message.reply_text(f'{command_handle} 不支持无输入调用。')

    msg_store.add(message)
    return await chat_core(client, message)


@ensure_not_bl
@ensure_gpt_auth
async def command_smart(client: Client, message: Message) -> Optional[Message]:
    if no_input(message):
        command = message.text
        command_handle = command.split(' ')[0].split('@')[0].lower()
        return await message.reply_text(f'{command_handle} 不支持无输入调用。')

    msg_store.add(message)
    return await chat_core(client, message, query_dialog=False)
