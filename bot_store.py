import logging
from pyrogram.types import Message


class MsgStore:
    def __init__(self):
        self.msgs = {}

    def add(self, msg: Message):
        if len(self.msgs) > 100:
            logging.warning('[bot_store]\tClearing message store')
            self.clear()
        try:
            chat_id = msg.chat.id
            msg_id = msg.id
        except AttributeError:
            return None
        if chat_id not in self.msgs:
            self.msgs[chat_id] = {}
        elif len(self.msgs[chat_id]) > 1000:
            logging.warning(f'[bot_store]\tClearing message store for chat {chat_id}')
            self.msgs[chat_id] = {}
        self.msgs[chat_id][msg_id] = msg

    def get(self, chat_id: int, msg_id: int):
        if chat_id in self.msgs:
            if msg_id in self.msgs[chat_id]:
                return self.msgs[chat_id][msg_id]
        return None

    def clear(self):
        self.msgs = {}
