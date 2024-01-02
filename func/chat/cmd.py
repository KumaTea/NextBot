import random
import asyncio
from pyrogram import Client
from typing import Optional
from gpt.auth import gpt_auth
from gpt.tools import gen_thread
from bot.session import msg_store
from bot.auth import ensure_not_bl
from common.info import gpt_admins
from gpt.auth import ensure_gpt_auth
from gpt.core import stream_chat_by_sentences
from pyrogram.types import Message, CallbackQuery
from pyrogram.enums.chat_action import ChatAction
from common.data import smart_inst, thinking_emojis
from func.chat.core import type_in_message, chat_core


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
    msg_store.add(message)
    command = message.text
    command_handle = command.split(' ')[0].split('@')[0].lower()
    content_index = command.find(' ')
    reply = message.reply_to_message
    if content_index == -1:
        # no text
        if not reply:
            return await message.reply_text(f'{command_handle} 不支持无输入调用。')

    return await chat_core(client, message)


@ensure_not_bl
@ensure_gpt_auth
async def command_smart(client: Client, message: Message) -> Optional[Message]:
    command = message.text
    content_index = command.find(' ')
    if content_index == -1:
        # no text
        return await message.reply_text('/smart 不支持无输入调用。')

    resp_message = await message.reply_text(random.choice(thinking_emojis) + '❓')
    thread = gen_thread([message], custom_inst=smart_inst)
    result, _ = await asyncio.gather(
        type_in_message(resp_message, stream_chat_by_sentences(thread)),
        message.reply_chat_action(ChatAction.TYPING)
    )
    return result
