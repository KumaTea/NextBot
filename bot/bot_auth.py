import logging
from pyrogram import Client
from pyrogram.types import Message
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
    async def wrapper(client: Client, message: Message):
        if message.from_user:
            user_id = message.from_user.id
            if user_id in bl_users:
                logging.warning(f'User {user_id} is in blacklist! Ignoring message.')
                return None
            else:
                return await func(client, message)
        elif message.sender_chat:
            if not message.forward_from_chat:
                return await func(client, message)
        else:
            # logging.warning('======= WARNING =======')
            # logging.warning('[bot_auth]\t\tNo from_user in message!')
            # logging.warning(f'{message=}')
            # logging.warning('========  END  ========')
            return None
    return wrapper
