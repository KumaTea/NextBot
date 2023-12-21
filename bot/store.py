import os
import pickle
import logging  # bot.session imported bot.store
from pyrogram.types import Message
from common.data import msg_data_dir


class MsgStore:
    def __init__(self):
        self.msgs = {}
        self.load()

    def add(self, msg: Message):
        try:
            chat_id = msg.chat.id
            msg_id = msg.id
        except AttributeError:
            return None
        if chat_id not in self.msgs:
            self.msgs[chat_id] = {}
        self.msgs[chat_id][msg_id] = msg

    def get(self, chat_id: int, msg_id: int):
        if chat_id in self.msgs:
            if msg_id in self.msgs[chat_id]:
                return self.msgs[chat_id][msg_id]
        return None

    def clear(self):
        cleared = 0
        if len(self.msgs) > 100:
            # find last 100 active chats
            active_chats = sorted(
                self.msgs.keys(),
                key=lambda x: max([msg.date for msg in self.msgs[x].values()]),
                reverse=True
            )[:100]
            # clear all other chats
            for chat_id in self.msgs:
                if chat_id not in active_chats:
                    del self.msgs[chat_id]
                    logging.warning(f'[bot_store]\tClearing inactive chat {chat_id}')
                    cleared += 1
        for chat_id in self.msgs:
            if len(self.msgs[chat_id]) > 10000:
                msg_ids = self.msgs[chat_id].keys()
                msg_ids = sorted(msg_ids)  # int
                msg_ids = msg_ids[len(msg_ids) - 10000:]
                for msg_id in self.msgs[chat_id]:
                    if msg_id not in msg_ids:
                        del self.msgs[chat_id][msg_id]
                logging.warning(f'[bot_store]\tClearing messages for chat {chat_id}')
                cleared += 1
        if cleared:
            self.save()

    def save(self):
        with open(f'{msg_data_dir}/msg.p', 'wb') as f:
            pickle.dump(self.msgs, f)

    def load(self):
        if os.path.isfile(f'{msg_data_dir}/msg.p'):
            with open(f'{msg_data_dir}/msg.p', 'rb') as f:
                self.msgs = pickle.load(f)
            logging.info(f'[bot_store]\tLoaded {len(self.msgs)} messages from file')
