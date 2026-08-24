import uuid
import random
import aiohttp
import asyncio
from typing import Callable
from telethon import utils
from common.info import max_dialog
from telethon.tl.custom import Message
from telethon.errors import FloodWaitError
from telethon import TelegramClient as Client
from bot.session import bot, config, logging, msg_store


# Telegram hands back a wait longer than this when it really means "stop"; a
# handler that slept through it would be stuck for the whole period.
max_flood_wait = 120  # seconds

api_timeout = aiohttp.ClientTimeout(total=30)


async def get_message(chat_id: int, msg_id: int, client: Client = bot) -> Message:
    msg = msg_store.get(chat_id, msg_id)
    if not msg:
        msg = await client.get_messages(chat_id, ids=msg_id)
        msg_store.add(msg)
        logging.info(f'[tg_tools]\t\tGet message {msg_id} via API')
    else:
        logging.info(f'[tg_tools]\t\tGet message {msg_id} via cache')
    return msg


async def get_dialog(client: Client, message: Message) -> list[Message]:
    dialog = [message]
    msg = message
    dialog_count = 0
    while msg and msg.reply_to_msg_id:
        reply = await get_message(msg.chat_id, msg.reply_to_msg_id, client)
        if not reply:
            break
        dialog.insert(0, reply)
        msg = reply
        dialog_count += 1
        if dialog_count >= max_dialog:
            break
    return dialog


def gen_uuid(length: int = 4) -> str:
    """
    Generate a random UUID string.
    :param length: The length of the UUID string.
    :return: A random UUID string.
    """
    return str(uuid.uuid4())[:length]


def retry_on_flood(tries: int = 1):
    """
    Retry the function after the flood wait time.

    :param tries: How many *retries* to make, so `tries=1` means two attempts
        in total. Waits longer than `max_flood_wait` are re-raised rather than
        slept through.
    """
    def decorator(func: Callable):
        async def wrapper(*args, **kwargs):
            # tries counts retries, so the first attempt is on top of it
            for attempt in range(tries + 1):
                try:
                    return await func(*args, **kwargs)
                except FloodWaitError as e:
                    if attempt >= tries or e.seconds > max_flood_wait:
                        raise
                    wait_time = e.seconds + 1 + random.random()
                    logging.warning(
                        f'[tg_tools]\t\tFlood wait of {func.__name__} '
                        f'for {wait_time:.1f} seconds'
                    )
                    await asyncio.sleep(wait_time)
        return wrapper
    return decorator


async def get_file_link(media) -> str:
    """
    A public https link to a piece of media, via the Bot API.

    Telethon has no Bot API file_id, but `pack_bot_file_id` can rebuild
    the legacy form for documents (voice notes and video notes included),
    which `getFile` still accepts.
    """
    file_id = utils.pack_bot_file_id(media)
    if not file_id:
        raise ValueError(f'Cannot build a file_id for {type(media).__name__}')

    bot_token = config['tg']['bot_token']

    tg_endpoint = f'https://api.telegram.org/bot{bot_token}'
    get_file_url = f'{tg_endpoint}/getFile?file_id={file_id}'

    async with aiohttp.ClientSession(timeout=api_timeout) as session:
        async with session.get(get_file_url) as resp:
            result = await resp.json()

    # getFile refuses anything over 20 MB, and says so in `description`
    # rather than by omitting `result`
    if not result.get('ok'):
        raise ValueError(result.get('description') or 'getFile failed')

    file_path = result['result']['file_path']
    return f'https://api.telegram.org/file/bot{bot_token}/{file_path}'
