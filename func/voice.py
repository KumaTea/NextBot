import random
from cmn.data import *
from cmn.info import max_voice
from pyrogram.types import Message
from cmn.data import TEMP_DIR


TASK_FILE = f'{TEMP_DIR}/task.txt'


async def process_voice(message: Message) -> Message:
    """
    Transcribe the voice message.
    :param message: The message object.
    :return: The message object.
    """
    voice = message.voice
    if voice.duration > max_voice:
        return None

    inform = await message.reply_text(random.choice(thinking_emojis) + '👂', quote=False)
    chat_id = message.chat.id
    voice_id = message.id
    inform_id = inform.id
    with open(TASK_FILE, 'a') as f:
        # append task to file
        f.write(','.join(['voice', chat_id, voice_id, inform_id]) + '\n')
    return inform
