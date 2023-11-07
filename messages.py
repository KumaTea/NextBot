from typing import Union
from session import logger
from pyrogram import Client
from bot_auth import ensure_not_bl
from pyrogram.types import Message
from bot_info import self_id, username
from func_chat import command_chat, ensure_gpt_auth


@ensure_gpt_auth
async def replied_chat(client: Client, message: Message) -> Union[Message, None]:
    message.text = f'/chat {message.text}'

    if message.entities:
        for entity in message.entities:
            entity.offset += 6

    return await command_chat(client, message)


@ensure_not_bl
async def process_msg(client: Client, message: Message) -> Union[Message, None]:
    user_id = message.from_user.id
    if user_id == self_id:
        return None
    text = message.text
    reply = message.reply_to_message
    if text and reply:
        try:
            if reply.from_user.id == self_id:
                return await replied_chat(client, message)
            elif text.startswith(f'@{username}') or text.endswith(f'@{username}'):
                # mentioning me
                message.text = text.replace(f'@{username}', '').strip()
                return await replied_chat(client, message)
        except AttributeError:
            # logger.warning('======== ERROR ========')
            # logger.warning('[messages]\tAttributeError')
            # logger.warning(f'{message=}')
            # logger.warning('========  END  ========')
            return None
    return None
