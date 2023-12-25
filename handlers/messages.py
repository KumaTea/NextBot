from typing import Optional
from pyrogram import Client
from pyrogram.types import Message
from bot.auth import ensure_not_bl
from func.voice import process_voice
from common.info import self_id, username
from common.data import voice_tag, gpt_auth_info
from func.chat import command_chat, ensure_gpt_auth


@ensure_gpt_auth
async def replied_chat(client: Client, message: Message) -> Optional[Message]:
    message.text = f'/chat {message.text}'

    if message.entities:
        for entity in message.entities:
            entity.offset += 6

    return await command_chat(client, message)


@ensure_not_bl
async def process_msg(client: Client, message: Message) -> Optional[Message]:
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
            # logging.warning('======== ERROR ========')
            # logging.warning('[messages]\tAttributeError')
            # logging.warning(f'{message=}')
            # logging.warning('========  END  ========')
            return None

    if message.voice:
        if (
            not message.forward_date  # not forwarded
            or message.forward_from  # forwarded, but can be checked
        ):
            return await process_voice(message)
    return None
