import os
import time
import requests
from bot.session import bot
from cmn.data import TEMP_DIR
from bot.tools import gen_uuid
from pyrogram.types import Message
from pyrogram.enums.parse_mode import ParseMode


API = 'http://172.21.45.250:14500/ocr'


def process_ocr(chat_id: int, reply_id: int, inform_id: int, lang: str = 'ch') -> Message:
    reply = bot.get_messages(chat_id, reply_id)
    inform = bot.get_messages(chat_id, inform_id)

    while 'ocr' in ' '.join(os.listdir(TEMP_DIR)):
        time.sleep(1)

    filename = f'/dev/shm/ocr-{gen_uuid()}.png'
    reply.download(filename)

    try:
        with open(filename, 'rb') as f:
            files = {'image': f}
            values = {'lang': lang}
            r = requests.post(API, files=files, data=values)
            result = r.json()['result']
            text = f'```\n{result}\n```'
            to_return = inform.edit_text(text, parse_mode=ParseMode.MARKDOWN)
    except Exception as e:
        to_return = inform.edit_text(f'Error: `{e}`', parse_mode=ParseMode.MARKDOWN)
    finally:
        os.remove(filename)

    return to_return
