import logging
from typing import Union
from pyrogram import Client
from pyrogram.types import Message, CallbackQuery
from pyrogram.raw.functions.contacts.get_blocked import GetBlocked

try:
    from local_db import trusted_group, bl_users
except ImportError:
    logging.warning('======== WARNING ========')
    logging.warning('[bot_auth]\t\tImportError')
    logging.warning('========  END  ========')
    trusted_group = []
    bl_users = []

# from cmn.session import config
#
# me = Client(
#     'me',
#     api_id=config['tg']['api_id'],
#     api_hash=config['tg']['api_hash']
# )


async def get_blocked_users(client: Client, offset: int = 0, limit: int = 100):
    result = await client.invoke(GetBlocked(offset=offset, limit=limit))
    return result.users


async def get_blocked_user_ids(client: Client, offset: int = 0, limit: int = 100):
    result = await get_blocked_users(client, offset, limit)
    # for i in result:
    #     yield i.id
    return [i.id for i in result]


def ensure_not_bl(func):
    async def wrapper(client: Client, obj: Union[Message, CallbackQuery]):
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
