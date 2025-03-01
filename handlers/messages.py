import asyncio
from typing import Optional
from pyrogram import Client
from gpt.data import voice_tag
from bot.session import msg_store
from pyrogram.types import Message
from func.voice import react_voice
from share.auth import ensure_auth
from func.chat.core import chat_core
from gpt.auth import ensure_gpt_auth
from common.data import gpt_auth_info
from common.info import self_id, username


# @ensure_auth has been decorated before this function is called
@ensure_gpt_auth
async def replied_chat(client: Client, message: Message) -> Optional[Message]:
    msg_store.add(message)
    return await chat_core(client, message)


@ensure_auth
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

    if message.voice or message.video_note:
        if (
            not message.forward_date  # not forwarded
            or message.forward_from  # forwarded, but can be checked
        ):
            # if forwarded by user with hidden identity, i.e. message.forward_date exists
            # then @ensure_auth cannot ensure both executor and original sender are authenticated
            # otherwise (not fw or fw and checked) the message is safe to be processed
            return await react_voice(message)
            # updating_msg = await message.reply_text(f'{voice_tag} 2.0 升级中，敬请谅解。', quote=False)
            # await asyncio.sleep(5)
            # await updating_msg.delete()
            # return updating_msg
    return None
