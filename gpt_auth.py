import os
from bot_info import gpt_admins
from bot_db import gpt_users_file


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


gpt_auth = GPTAuth()
