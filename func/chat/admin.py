from typing import Optional
from gpt.auth import gpt_auth
from common.info import gpt_admins
from telethon.tl.custom import Message


async def command_allow_gpt(event) -> Optional[Message]:
    if event.sender_id not in gpt_admins:
        return None

    reply = await event.get_reply_message()
    if not reply:
        return await event.reply('请回复一个用户！')

    replied_user_id = reply.sender_id
    if replied_user_id in gpt_auth.users:
        return await event.reply('该用户已经在列表中了！')

    gpt_auth.add_user(replied_user_id)
    return await event.reply('已将该用户添加到授权列表。')
