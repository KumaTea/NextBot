import asyncio
from typing import Optional
from bot.session import msg_store
from common.info import gpt_admins
from share.auth import ensure_auth
from gpt.tools import trim_command
from telethon.tl.custom import Message
from gpt.auth import gpt_auth  # , ensure_gpt_auth
from func.chat.core import no_input, chat_core, get_last_n_messages, format_last_n_messages


async def callback_gpt_auth(event) -> tuple:
    task, subtask, user_id, confirm = event.data.decode().split('_')
    user_id = int(user_id)
    async_tasks = []
    if event.sender_id in gpt_admins:
        if confirm == 'y':
            gpt_auth.add_user(user_id)
            async_tasks.append(event.edit('现在我可以和你聊天啦！'))
            async_tasks.append(event.answer('已授权'))  # for admin
        else:
            async_tasks.append(event.edit('我还不能跟你聊天捏。'))
            async_tasks.append(event.answer('已拒绝'))
    else:
        async_tasks.append(event.answer('不是你的别乱按！', alert=True))
    return await asyncio.gather(*async_tasks)


async def gpt_callback_handler(event):
    subtask = event.data.decode().split('_')[1]

    if subtask == 'auth':
        return await callback_gpt_auth(event)


# @ensure_gpt_auth
@ensure_auth
async def command_chat(event) -> Optional[Message]:
    message = event.message
    if no_input(message):
        command_handle = message.raw_text.split(' ')[0].split('@')[0].lower()
        return await message.reply(f'{command_handle} 不支持无输入调用。')

    text = trim_command(message.raw_text)
    if text.isdigit() and 2 < int(text) < 99:
        # get last n messages
        last_n_messages = await get_last_n_messages(event.client, message, int(text))
        message = format_last_n_messages(message, last_n_messages)
        resp_text = f'正在读取之前的{text}条消息...'
    else:
        resp_text = ''
    msg_store.add(message)
    return await chat_core(event.client, message, resp_text=resp_text)


# @ensure_gpt_auth
@ensure_auth
async def command_smart(event) -> Optional[Message]:
    message = event.message
    if no_input(message):
        command_handle = message.raw_text.split(' ')[0].split('@')[0].lower()
        return await message.reply(f'{command_handle} 不支持无输入调用。')

    msg_store.add(message)
    return await chat_core(event.client, message, query_dialog=False)
