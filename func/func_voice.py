import os
import uuid
import random
import asyncio
import logging
from cmn.session import gpt
from pyrogram.types import Message
from bot.bot_db import thinking_emojis


def gen_uuid(length: int = 4) -> str:
    """
    Generate a random UUID string.
    :param length: The length of the UUID string.
    :return: A random UUID string.
    """
    return str(uuid.uuid4())[:length]


async def save_voice(message: Message) -> str:
    """
    Save the voice message to a file.
    :param message: The message object.
    :return: The path of the saved file.
    """
    voice = message.voice
    file_id = voice.file_id
    file_name = gen_uuid()
    file_path = f'/dev/shm/{file_name}.ogg'
    await message.download(file_path)
    return file_path


async def transcribe_voice(voice_path: str) -> str:
    with open(voice_path, 'rb') as voice:
        transcript = await gpt.audio.transcriptions.create(
            model='whisper-1',
            file=voice,
            language='zh'
        )
    text = transcript.text
    logging.info(f'[func_voice]\t{text}')
    return text


async def process_voice(message: Message) -> Message:
    """
    Transcribe the voice message.
    :param message: The message object.
    :return: The message object.
    """
    inform = None
    voice_path = None
    try:
        inform, voice_path = await asyncio.gather(
            message.reply_text(random.choice(thinking_emojis) + '👂', quote=False),
            save_voice(message)
        )
        user_mention = message.from_user.mention(style="md")
        transcription = await transcribe_voice(voice_path)
        text = user_mention + ':\n' + transcription
        return await inform.edit_text(text)
    except Exception as e:
        logging.warning(f'[func_voice]\tERROR!!!')
        logging.warning(f'[func_voice]\t{e}')
        if isinstance(inform, Message):
            await inform.edit_text('听不懂捏')
    finally:
        if voice_path and os.path.isfile(voice_path):
            os.remove(voice_path)
