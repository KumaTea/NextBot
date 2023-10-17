import os
from bot_db import pwd, gpt_data_dir
from register import register_handlers


def starting():
    os.makedirs(gpt_data_dir, exist_ok=True)

    register_handlers()
