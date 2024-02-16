import os
import asyncio
import requests
from pyrogram import Client
from bot.tools import gen_uuid
from common.data import TEMP_DIR
from pyrogram.types import Message
from pyrogram.enums.parse_mode import ParseMode


API = 'http://cap.lan.kmtea.eu:14500/cap'


async def process_cap(bot: Client, chat_id: int, reply_id: int, inform_id: int, model: str = 'blip') -> Message:
    reply, inform = await asyncio.gather(
        bot.get_messages(chat_id, reply_id),
        bot.get_messages(chat_id, inform_id)
    )

    while any(f in ' '.join(os.listdir(TEMP_DIR)) for f in ['ocr', 'cap']):
        await asyncio.sleep(1)

    filename = f'/dev/shm/cap-{gen_uuid()}.png'
    try:
        await reply.download(filename)
    except ValueError as e:
        if 'downloadable' in str(e):
            return await inform.edit_text('看不到图，可以试试重新拉我进群。', parse_mode=ParseMode.MARKDOWN)
    except Exception as e:
        return await inform.edit_text(f'Error: `{e}`', parse_mode=ParseMode.MARKDOWN)

    to_return = None
    result = None
    try:
        with open(filename, 'rb') as f:
            files = {'image': f}
            values = {'model': model}
            r = requests.post(API, files=files, data=values, timeout=240)
            if r.status_code != 200:
                raise ConnectionError(f'HTTP {r.status_code} from API')

            result = r.json()['result']
            text = f'```\n{result}\n```'
            to_return = await inform.edit_text(text, parse_mode=ParseMode.MARKDOWN)
    except Exception as e:
        if 'MESSAGE_NOT_MODIFIED' not in str(e):
            to_return = await inform.edit_text(f'Error: `{e}` Result: `{result}`', parse_mode=ParseMode.MARKDOWN)
    finally:
        os.remove(filename)

    return to_return
