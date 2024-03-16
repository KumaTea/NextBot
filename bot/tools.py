import uuid
import random
import asyncio
from pyrogram import Client
from typing import Callable
from common.info import max_dialog
from pyrogram.types import Message
from pyrogram.errors import FloodWait
from bot.session import bot, logging, msg_store


async def get_message(chat_id: int, msg_id: int, client: Client = bot) -> Message:
    msg = msg_store.get(chat_id, msg_id)
    if not msg:
        msg = await client.get_messages(chat_id, msg_id)
        msg_store.add(msg)
        logging.info(f'[tg_tools]\t\tGet message {msg_id} via API')
    else:
        logging.info(f'[tg_tools]\t\tGet message {msg_id} via cache')
    return msg


async def get_dialog(client: Client, message: Message) -> list[Message]:
    dialog = [message]
    msg = message
    dialog_count = 0
    while msg.reply_to_message:
        reply = await get_message(msg.chat.id, msg.reply_to_message.id)
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
    :param tries: The number of retries.
    """
    def decorator(func: Callable):
        async def wrapper(*args, **kwargs):
            inner_tries = tries
            e = None
            while inner_tries:
                try:
                    return await func(*args, **kwargs)
                except FloodWait as e:
                    wait_time = e.value + 1 + random.random()
                    logging.warning(f'[tg_tools]\t\tFlood wait of {func.__name__} for {wait_time} seconds')
                    await asyncio.sleep(wait_time)
                    inner_tries -= 1
                # except Exception as e:
                #     raise e
            # retry count exceeded
            if e:
                raise e
            # else:
            #     return None
        return wrapper
    return decorator
