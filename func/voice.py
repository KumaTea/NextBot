import os
import random
import asyncio
from common.info import max_voice
from pyrogram.types import Message
from gpt.data import thinking_emojis
from bot.tools import retry_on_flood
from common.data import TEMP_DIR, MEDIA_BOT_CMD


TASK_FILE = f'{TEMP_DIR}/task.txt'
STATUS_FILE = f'{TEMP_DIR}/media.run'


@retry_on_flood(tries=2)
async def react_voice(message: Message) -> Message:
    """
    Transcribe the voice message.
    :param message: The message object.
    :return: The message object.
    """
    voice = message.voice
    if voice.duration > max_voice:
        return await message.reply_text(f'太长不听', quote=True)

    inform = await message.reply_text(random.choice(thinking_emojis) + '👂', quote=True)
    chat_id = message.chat.id
    voice_id = message.id
    inform_id = inform.id

    while os.path.isfile(STATUS_FILE):
        await asyncio.sleep(1 + random.random())

    with open(TASK_FILE, 'a') as f:
        # append task to file
        f.write(','.join(list(map(str, ['voice', chat_id, voice_id, inform_id]))) + '\n')

    await asyncio.create_subprocess_shell(MEDIA_BOT_CMD)
    return inform
