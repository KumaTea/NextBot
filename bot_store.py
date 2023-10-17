from pyrogram.types import Message


class MsgStore:
    def __init__(self):
        self.msgs = {}

    def add(self, msg: Message):
        chat_id = msg.chat.id
        msg_id = msg.id
        if chat_id not in self.msgs:
            self.msgs[chat_id] = {}
        self.msgs[chat_id][msg_id] = msg

    def get(self, chat_id: int, msg_id: int):
        if chat_id in self.msgs:
            if msg_id in self.msgs[chat_id]:
                return self.msgs[chat_id][msg_id]
        return None
