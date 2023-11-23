import os
import asyncio
from cmn.data import TEMP_DIR
from mbot.ocr import process_ocr
from mbot.voice import process_voice


TASK_FILE = f'{TEMP_DIR}/task.txt'


async def process_task(task: str):
    if task.startswith('ocr'):
        task_name, chat_id, reply_id, inform_id, lang = task.split(',')
        return await process_ocr(int(chat_id), int(reply_id), int(inform_id), lang)
    elif task.startswith('voice'):
        task_name, chat_id, reply_id, inform_id = task.split(',')
        return await process_voice(int(chat_id), int(reply_id), int(inform_id))


async def handler():
    while True:
        if os.path.isfile(TASK_FILE):
            with open(TASK_FILE, 'r') as f:
                tasks = f.read()
            os.remove(TASK_FILE)
            for task in tasks.splitlines():
                if task:
                    await process_task(task)
        await asyncio.sleep(30)
