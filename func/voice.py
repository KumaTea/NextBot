import uuid
import random
import asyncio
import logging
from cmn.data import *
from typing import Optional
from cmn.info import max_voice
from pyrogram.types import Message
from cmn.session import gpt, msg_store
from pyrogram.enums.parse_mode import ParseMode


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

    if not text.strip():
        return '啥也没说'
    for word in whisper_blacklist:
        if word in text:
            return '啥也没说'

    return text


async def process_voice(message: Message) -> Optional[Message]:
    """
    Transcribe the voice message.
    :param message: The message object.
    :return: The message object.
    """
    voice = message.voice
    if voice.duration > max_voice:
        return None
    inform = None
    voice_path = None
    try:
        inform, voice_path = await asyncio.gather(
            message.reply_text(random.choice(thinking_emojis) + '👂', quote=False),
            save_voice(message)
        )
        if message.from_user:
            user_mention = message.from_user.mention(style=ParseMode.MARKDOWN)
            if message.forward_from:
                user_mention += ' 🔊 ' + message.forward_from.mention(style=ParseMode.MARKDOWN)
        elif message.sender_chat:
            if message.sender_chat.username:
                user_mention = f'[{message.sender_chat.title}](tg://resolve?domain={message.sender_chat.username})'
            else:
                user_mention = message.sender_chat.title
        else:
            user_mention = '😎'
        transcription = await transcribe_voice(voice_path)
        text = user_mention + ':\n' + transcription + '\n' + voice_tag
        setattr(message, 'transcription', transcription)
        msg_store.add(message)
        return await inform.edit_text(text, parse_mode=ParseMode.MARKDOWN)
    except Exception as e:
        logging.warning(f'[func_voice]\tERROR!!!')
        logging.warning(f'[func_voice]\t{e}')
        if isinstance(inform, Message):
            return await inform.edit_text('听不懂捏')
    finally:
        if voice_path and os.path.isfile(voice_path):
            os.remove(voice_path)
