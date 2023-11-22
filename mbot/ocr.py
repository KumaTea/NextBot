import os
import time
import asyncio
import requests
from mbot.session import bot
from cmn.data import TEMP_DIR
from bot.tools import gen_uuid
from pyrogram.types import Message
from pyrogram.enums.parse_mode import ParseMode


API = 'http://172.21.45.250:14500/ocr'


async def process_ocr(chat_id: int, reply_id: int, inform_id: int, lang: str = 'ch') -> Message:
    reply, inform = await asyncio.gather(
        bot.get_messages(chat_id, reply_id),
        bot.get_messages(chat_id, inform_id)
    )

    while 'ocr' in ' '.join(os.listdir(TEMP_DIR)):
        time.sleep(1)

    filename = f'/dev/shm/ocr-{gen_uuid()}.png'
    await reply.download(filename)

    to_return = None
    try:
        with open(filename, 'rb') as f:
            files = {'image': f}
            values = {'lang': lang}
            r = requests.post(API, files=files, data=values)
            result = r.json()['result']
            text = f'```\n{result}\n```'
            to_return = await inform.edit_text(text, parse_mode=ParseMode.MARKDOWN)
    except Exception as e:
        if 'MESSAGE_NOT_MODIFIED' not in str(e):
            to_return = await inform.edit_text(f'Error: `{e}`', parse_mode=ParseMode.MARKDOWN)
    finally:
        os.remove(filename)

    return to_return
