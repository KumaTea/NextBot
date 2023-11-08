import os
from cmn.register import register_handlers
from bot.bot_db import gpt_data_dir, msg_data_dir


def starting():
    os.makedirs(gpt_data_dir, exist_ok=True)
    os.makedirs(msg_data_dir, exist_ok=True)

    register_handlers()
