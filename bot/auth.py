from typing import Union
from pyrogram import Client
from bot.session import logging
from cmn.local import bl_users, known_group
from pyrogram.types import Message, CallbackQuery


def ensure_not_bl(func):
    async def wrapper(client: Client, obj: Union[Message, CallbackQuery]):
        if obj.chat and obj.chat.id not in known_group:
            logging.warning(f'Chat id={obj.chat.id} name={obj.chat.title} not known!')
        if obj.from_user:
            user_id = obj.from_user.id
            if user_id in bl_users:
                logging.warning(f'User {user_id} is in blacklist! Ignoring message.')
                return None
        if isinstance(obj, Message):
            if obj.reply_to_message:
                if obj.reply_to_message.from_user:
                    user_id = obj.reply_to_message.from_user.id
                    if user_id in bl_users:
                        logging.warning(f'Replied user {user_id} is in blacklist! Ignoring message.')
                        return None
        return await func(client, obj)
    return wrapper
