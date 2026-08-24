import os
import logging
from x.sync import start as start_mirror
from func.wiki import fetch_wiki  # noqa -- used by the commented-out call below
from handlers.register import register_handlers
from common.data import TEMP_DIR, gpt_data_dir, msg_data_dir
from bot.session import bot, msg_store


async def resolve_self():
    """
    Learn our own id from Telegram instead of trusting the constant.

    `common.info.self_id` is what tells the chat code which messages are its
    own; a stale value there makes the bot answer itself. The constant stays as
    a fallback for when this lookup fails.
    """
    from common import info
    try:
        me = await bot.get_me()
    except Exception:
        logging.exception('[starting]\tCould not resolve own id, keeping the constant')
        return info.self_id

    if me and me.id != info.self_id:
        logging.warning(f'[starting]\tself_id was {info.self_id}, Telegram says {me.id}')
        info.self_id = me.id
    return info.self_id


async def starting():
    os.makedirs(gpt_data_dir, exist_ok=True)
    os.makedirs(msg_data_dir, exist_ok=True)
    os.makedirs(TEMP_DIR, exist_ok=True)

    await resolve_self()
    register_handlers()
    msg_store.start_autosave()
    await start_mirror()

    # temporarily skip fetching wiki
    # await fetch_wiki()
