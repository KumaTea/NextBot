import os
from typing import Optional
from telethon import Button
from common.info import gpt_admins
from share.common import no_preview
from share.local import trusted_group
from telethon.tl.custom import Message
from common.data import gpt_auth_info, bot_debug_info, gpt_users_file


class GPTAuth:
    def __init__(self, users: set[int] = None):
        self.users = users or set()
        self.read_users()
        if not self.users:
            self.users = gpt_admins.copy()

    def read_users(self):
        if os.path.isfile(gpt_users_file):
            with open(gpt_users_file, 'r') as file:
                users = file.read().splitlines()
            self.users = set(int(user) for user in users)

    def write_users(self):
        with open(gpt_users_file, 'w') as file:
            file.write('\n'.join(str(user) for user in self.users))

    def add_user(self, user_id: int):
        if user_id not in self.users:
            self.users.add(user_id)
            self.write_users()

    def del_user(self, user_id: int):
        if user_id in self.users:
            self.users.remove(user_id)
            self.write_users()


gpt_auth = GPTAuth()


def has_gpt_auth(event) -> bool:
    if event.chat_id in trusted_group:
        return True
    return bool(event.sender_id) and event.sender_id in gpt_auth.users


async def ask_for_gpt_auth(event) -> Optional[Message]:
    if os.name == 'nt':
        # debugging
        return await event.reply(bot_debug_info, **no_preview)

    user_id = event.sender_id
    return await event.reply(gpt_auth_info, buttons=[
        [Button.inline('允许', f'gpt_auth_{user_id}_y'.encode())],
        [Button.inline('拒绝', f'gpt_auth_{user_id}_n'.encode())]
    ])


def ensure_gpt_auth(func):
    async def wrapper(event):
        if has_gpt_auth(event):
            return await func(event)
        # return await ask_for_gpt_auth(event)
        return None
    return wrapper
