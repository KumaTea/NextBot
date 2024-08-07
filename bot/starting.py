import os
import asyncio
from handlers.register import register_handlers
from common.data import TEMP_DIR, gpt_data_dir, msg_data_dir
from func.wiki import fetch_wiki


async def async_starting():
    await fetch_wiki()


def starting():
    os.makedirs(gpt_data_dir, exist_ok=True)
    os.makedirs(msg_data_dir, exist_ok=True)
    os.makedirs(TEMP_DIR, exist_ok=True)

    register_handlers()

    loop = asyncio.get_event_loop()
    loop.run_until_complete(async_starting())
