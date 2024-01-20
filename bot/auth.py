from typing import Union
from pyrogram import Client
from bot.session import logging
from pyrogram.types import Message, CallbackQuery
from common.local import bl_users, known_group, known_user_ids


def ensure_not_bl(func):
    async def wrapper(client: Client, obj: Union[Message, CallbackQuery]):

        # target the message
        if isinstance(obj, CallbackQuery):
            msg = obj.message
        else:
            msg = obj

        # detect unknown group
        if msg.chat and msg.chat.id < 0 and msg.chat.id not in known_group:
            logging.warning(f'Chat id={msg.chat.id} name={msg.chat.title} not known!')
            known_group.append(msg.chat.id)

        # users
        if msg.from_user:
            user_id = msg.from_user.id
            # blocked?
            if user_id in bl_users:
                logging.warning(f'User {user_id} is in blacklist! Ignoring message.')
                return None
            # no pic?
            user_pic = msg.from_user.photo
            if not user_pic:
                logging.warning(f'User {user_id} has no profile picture! Ignoring message.')
                return None
            # premium?
            is_premium = msg.from_user.is_premium
            is_known = user_id in known_user_ids
            if is_premium and not is_known:
                logging.warning(f'User {user_id} is a premium user! Ignoring message.')
                return None

        # replies
        if msg.reply_to_message and msg.reply_to_message.from_user:
            user_id = msg.reply_to_message.from_user.id
            if user_id in bl_users:
                logging.warning(f'Replied user {user_id} is in blacklist! Ignoring message.')
                return None

        # forwards
        if msg.forward_from:
            user_id = msg.forward_from.id
            if user_id in bl_users:
                logging.warning(f'Forwarded user {user_id} is in blacklist! Ignoring message.')
                return None

        # all good
        return await func(client, obj)
    return wrapper
