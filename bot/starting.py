import os
from handlers.register import register_handlers
from cmn.data import gpt_data_dir, msg_data_dir


def starting():
    os.makedirs(gpt_data_dir, exist_ok=True)
    os.makedirs(msg_data_dir, exist_ok=True)

    register_handlers()
