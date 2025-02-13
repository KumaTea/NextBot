import os
import time
from pathlib import Path
from pyrogram import Client
from bot.session import logging
from mbot.ocr import process_ocr
from mbot.cap import process_cap
from mbot.voice import process_voice
from common.data import TEMP_DIR, REBOOT_CMD


TASK_FILE = f'{TEMP_DIR}/task.txt'
STATUS_FILE = f'{TEMP_DIR}/media.run'


async def process_task(bot: Client, task: str):
    if task.startswith('ocr'):
        task_name, chat_id, reply_id, inform_id, lang = task.split(',')
        return await process_ocr(bot, int(chat_id), int(reply_id), int(inform_id), lang)
    elif task.startswith('cap'):
        task_name, chat_id, reply_id, inform_id, model = task.split(',')
        return await process_cap(bot, int(chat_id), int(reply_id), int(inform_id), model)
    elif task.startswith('voice'):
        task_name, chat_id, reply_id, inform_id = task.split(',')
        return await process_voice(bot, int(chat_id), int(reply_id), int(inform_id))


class StatHolder:
    def __init__(self, sign: str, delay: int = 1):
        self.sign = sign
        self.delay = delay
        self.pid = os.getpid()

    def __enter__(self):
        while os.path.isfile(self.sign):
            logging.info(f'Media bot pid={self.pid} waiting...')
            time.sleep(self.delay)
        Path(self.sign).touch()
        logging.info(f'Media bot pid={self.pid} started!')

    def __exit__(self, exc_type, exc_val, exc_tb):
        os.remove(self.sign)
        logging.info(f'Media bot pid={self.pid} stopped.')


async def handler(bot: Client):
    try:
        if os.path.isfile(TASK_FILE):
            with open(TASK_FILE, 'r') as f:
                tasks = f.read()
            os.remove(TASK_FILE)
            for task in tasks.splitlines():
                if task:
                    try:
                        await process_task(bot, task)
                    except RuntimeError as e:
                        if 'Event loop is closed' in str(e):
                            logging.error('Event loop is closed')
                            logging.error('Rebooting...')
                            return os.system(REBOOT_CMD)
    except Exception as e:
        logging.error(e)
