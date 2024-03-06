from typing import Optional
from pyrogram import Client
from gpt.auth import gpt_auth
from pyrogram.types import Message
from common.info import gpt_admins


async def command_allow_gpt(client: Client, message: Message) -> Optional[Message]:
    user_id = message.from_user.id
    if user_id not in gpt_admins:
        return None

    reply = message.reply_to_message
    if not reply:
        return await message.reply_text('请回复一个用户！')

    replied_user = reply.from_user
    if replied_user.id in gpt_auth.users:
        return await message.reply_text('该用户已经在列表中了！')

    gpt_auth.add_user(replied_user.id)
    return await message.reply_text(f'已将该用户添加到授权列表。')
