from typing import Optional
from gpt.data import voice_tag
from bot.session import msg_store
from func.voice import react_voice
from share.auth import ensure_auth
from func.chat.core import chat_core
# from gpt.auth import ensure_gpt_auth
from common.data import gpt_auth_info
from telethon.tl.custom import Message
from common import info
from common.info import username


# @ensure_auth has been decorated before this function is called
# @ensure_gpt_auth
async def replied_chat(event) -> Optional[Message]:
    msg_store.add(event.message)
    return await chat_core(event.client, event.message)


@ensure_auth
async def process_msg(event) -> Optional[Message]:
    if event.sender_id == info.self_id:
        return None

    message = event.message
    text = message.raw_text
    if text:
        if text.startswith('/'):
            return None

        reply = await message.get_reply_message()
        if reply and reply.sender_id == info.self_id:
            reply_text = reply.raw_text or ''
            if voice_tag in reply_text:
                return None
            if gpt_auth_info == reply_text:
                return None
            return await replied_chat(event)
        if text.startswith(f'@{username}') or text.endswith(f'@{username}'):
            # mentioning me
            # drop the mention; the old entity offsets no longer line up
            message.message = text.replace(f'@{username}', '').strip()
            message.entities = None
            return await replied_chat(event)

    media = message.voice or message.video_note
    if media:
        forward = message.forward
        if (
            not forward  # not forwarded
            or forward.sender_id  # forwarded, but can be checked
        ):
            # if forwarded by a user with hidden identity, i.e. message.forward exists
            # but carries no sender, then @ensure_auth cannot ensure both executor and
            # original sender are authenticated
            # otherwise (not fw or fw and checked) the message is safe to be processed
            return await react_voice(event)
    return None
