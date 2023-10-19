import os
from typing import Union
from pyrogram import Client
from bot_info import gpt_admins
from pyrogram.types import Message
from bot_db import gpt_users_file, gpt_auth_info
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton


class GPTAuth:
    def __init__(self):
        self.users = []
        self.read_users()
        if not self.users:
            self.users = gpt_admins.copy()

    def read_users(self):
        if os.path.isfile(gpt_users_file):
            with open(gpt_users_file, 'r') as file:
                users = file.read().splitlines()
            self.users = [int(user) for user in users]

    def write_users(self):
        with open(gpt_users_file, 'w') as file:
            file.write('\n'.join([str(user) for user in self.users]))

    def add_user(self, user_id: int):
        if user_id not in self.users:
            self.users.append(user_id)
            self.write_users()

    def del_user(self, user_id: int):
        if user_id in self.users:
            self.users.remove(user_id)
            self.write_users()


def has_gpt_auth(client: Client, message: Message) -> bool:
    if message.from_user:
        user_id = message.from_user.id
        if user_id in gpt_auth.users:
            return True
    return False


async def ask_for_gpt_auth(client: Client, message: Message) -> Union[Message, None]:
    user_id = message.from_user.id
    reply_markup = InlineKeyboardMarkup([
        [InlineKeyboardButton('允许', callback_data=f'gpt_auth_{user_id}_y')],
        [InlineKeyboardButton('拒绝', callback_data=f'gpt_auth_{user_id}_n')]
    ])
    return await message.reply_text(gpt_auth_info, reply_markup=reply_markup)


def ensure_gpt_auth(func):
    async def wrapper(client: Client, message: Message):
        if has_gpt_auth(client, message):
            return await func(client, message)
        else:
            return await ask_for_gpt_auth(client, message)
    return wrapper


gpt_auth = GPTAuth()
