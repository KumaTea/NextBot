import random
import requests
from cmn.data import *
from cmn.info import max_voice
from pyrogram.types import Message


LOCAL_API = 'http://127.0.0.1:13600/voice'


async def process_voice(message: Message):
    """
    Transcribe the voice message.
    :param message: The message object.
    :return: The message object.
    """
    voice = message.voice
    if voice.duration > max_voice:
        return None
    inform = await message.reply_text(random.choice(thinking_emojis) + '👂', quote=False)

    r = requests.get(
        LOCAL_API,
        params={
            'chat_id': message.chat.id,
            'voice_id': message.id,
            'inform_id': inform.id,
        }
    )
    return r
