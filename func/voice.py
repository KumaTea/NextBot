import random
import aiohttp
import asyncio
from pyrogram.types import Message
from bot.tools import get_file_link
from common.info import max_voice_len
from gpt.data import voice_tag, thinking_emojis, whisper_blacklist


TRANSCRIBE_API = 'http://10.3.3.6:12001/transcribe'


async def react_voice(message: Message) -> Message:
    """
    Transcribe the voice message.
    :param message: The message object.
    :return: The message object.
    """
    media = message.voice or message.video_note
    duration = media.duration
    if duration > max_voice_len:
        return await message.reply_text(f'太长不听', quote=True)

    # inform = await message.reply_text(random.choice(thinking_emojis) + '👂', quote=True)
    # file_link = await get_file_link(voice.file_id)
    inform, file_link = await asyncio.gather(
        message.reply_text(random.choice(thinking_emojis) + '👂', quote=True),
        get_file_link(media.file_id)
    )

    async with aiohttp.ClientSession() as session:
        async with session.get(f'{TRANSCRIBE_API}?url={file_link}') as resp:
            text = await resp.text()

    if any(word in text for word in whisper_blacklist):
        return await inform.edit_text('听不懂捏')

    if '\n' in text.strip():
        seperator = '\n'
    else:
        seperator = ' '
    return await inform.edit_text(f'{text.strip()}{seperator}{voice_tag}')
