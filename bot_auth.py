import logging
from pyrogram import Client
from pyrogram.types import Message
from pyrogram.raw.functions.contacts.get_blocked import GetBlocked

try:
    from local_db import trusted_group, bl_users
except ImportError:
    trusted_group = []
    bl_users = []

# me = Client(
#     'me',
#     api_id=config['kuma']['api_id'],
#     api_hash=config['kuma']['api_hash']
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
        else:
            return await func(client, message)
    return wrapper


# https://stackoverflow.com/questions/4122815/
def multi_dec(decorators: list) -> callable:
    def decorator(f):
        for d in decorators:
            f = d(f)
        return f
    return decorator
