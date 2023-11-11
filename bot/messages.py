from typing import Union
from pyrogram import Client
from bot.bot_db import voice_tag, gpt_auth_info
from pyrogram.types import Message
from bot.bot_auth import ensure_not_bl
from func.func_voice import process_voice
from bot.bot_info import self_id, username
from func.func_chat import command_chat, ensure_gpt_auth


@ensure_gpt_auth
async def replied_chat(client: Client, message: Message) -> Union[Message, None]:
    message.text = f'/chat {message.text}'

    if message.entities:
        for entity in message.entities:
            entity.offset += 6

    return await command_chat(client, message)


@ensure_not_bl
async def process_msg(client: Client, message: Message) -> Union[Message, None]:
    if message.from_user:
        user_id = message.from_user.id
        if user_id == self_id:
            return None

    text = message.text
    reply = message.reply_to_message
    if text:
        if text.startswith('/'):
            return None

        try:
            if reply and reply.from_user.id == self_id:
                if voice_tag in reply.text:
                    return None
                elif gpt_auth_info == reply.text:
                    return None
                else:
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

    if message.voice:
        return await process_voice(message)
    return None
