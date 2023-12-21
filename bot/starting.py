import os
from handlers.register import register_handlers
from common.data import gpt_data_dir, msg_data_dir, TEMP_DIR


def starting():
    os.makedirs(gpt_data_dir, exist_ok=True)
    os.makedirs(msg_data_dir, exist_ok=True)
    os.makedirs(TEMP_DIR, exist_ok=True)

    register_handlers()
