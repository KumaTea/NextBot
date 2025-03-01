import os
import random
import aiohttp
import asyncio
from common.info import max_voice
from pyrogram.types import Message
from gpt.data import thinking_emojis
from bot.tools import get_file_link


TRANSCRIBE_API = 'http://10.3.3.6:12001/transcribe'


async def react_voice(message: Message) -> Message:
    """
    Transcribe the voice message.
    :param message: The message object.
    :return: The message object.
    """
    voice = message.voice
    if voice.duration > max_voice:
        return await message.reply_text(f'太长不听', quote=True)

    # inform = await message.reply_text(random.choice(thinking_emojis) + '👂', quote=True)
    # file_link = await get_file_link(voice.file_id)
    inform, file_link = asyncio.gather(
        message.reply_text(random.choice(thinking_emojis) + '👂', quote=True),
        get_file_link(voice.file_id)
    )

    async with aiohttp.ClientSession() as session:
        async with session.get(f'{TRANSCRIBE_API}?url={file_link}') as resp:
            text = await resp.text()

    return await inform.edit_text(text)
