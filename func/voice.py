import os
import random
import asyncio
from cmn.info import max_voice
from pyrogram.types import Message
from cmn.data import TEMP_DIR, MEDIA_BOT_CMD, thinking_emojis


TASK_FILE = f'{TEMP_DIR}/task.txt'
STATUS_FILE = f'{TEMP_DIR}/media.run'


async def process_voice(message: Message) -> Message:
    """
    Transcribe the voice message.
    :param message: The message object.
    :return: The message object.
    """
    voice = message.voice
    if voice.duration > max_voice:
        return await message.reply_text(f'太长不听', quote=False)

    inform = await message.reply_text(random.choice(thinking_emojis) + '👂', quote=False)
    chat_id = message.chat.id
    voice_id = message.id
    inform_id = inform.id
    with open(TASK_FILE, 'a') as f:
        # append task to file
        f.write(','.join(list(map(str, ['voice', chat_id, voice_id, inform_id]))) + '\n')

    while os.path.isfile(STATUS_FILE):
        await asyncio.sleep(1)
    await asyncio.create_subprocess_shell(MEDIA_BOT_CMD)
    return inform
