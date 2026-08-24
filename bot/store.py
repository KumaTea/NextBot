import os
import copy
import pickle
import asyncio
import logging  # bot.session imported bot.store
from telethon.tl.custom import Message
from common.data import msg_data_dir


# Pickling the whole store takes as long as the store is big, and it happens on
# the event loop, so it is done on a timer rather than after every reply.
autosave_interval = 60  # seconds
prune_interval = 30 * 60  # seconds

max_chats = 100
max_msgs_per_chat = 10000


def detached(msg: Message) -> Message:
    """
    A copy of a message that can be pickled.

    Telethon hangs a live `TelegramClient` off every message and that is
    not picklable, so the cached copy drops the client (and the lazily
    fetched reply, which carries a client of its own).
    """
    clone = copy.copy(msg)
    clone._client = None
    clone._reply_message = None
    return clone


class MsgStore:
    def __init__(self, client=None):
        self.msgs: dict[int, dict[int, Message]] = {}
        self.client = client
        self.dirty = False
        self._task = None
        self.load()

    def add(self, msg: Message):
        try:
            chat_id = msg.chat_id
            msg_id = msg.id
        except AttributeError:
            return None
        if chat_id is None or msg_id is None:
            return None
        self.msgs.setdefault(chat_id, {})[msg_id] = detached(msg)
        self.dirty = True

    def get(self, chat_id: int, msg_id: int):
        stored = self.msgs.get(chat_id, {}).get(msg_id)
        if stored is None:
            return None
        # hand out a live copy, keep the stored one picklable
        msg = copy.copy(stored)
        msg._client = self.client
        return msg

    def clear(self):
        cleared = 0
        if len(self.msgs) > max_chats:
            # find the most recently active chats
            active_chats = sorted(
                self.msgs.keys(),
                key=self._last_active,
                reverse=True
            )[:max_chats]
            # clear all other chats
            for chat_id in list(self.msgs):
                if chat_id not in active_chats:
                    del self.msgs[chat_id]
                    logging.warning(f'[bot_store]\tClearing inactive chat {chat_id}')
                    cleared += 1
        for chat_id in self.msgs:
            if len(self.msgs[chat_id]) > max_msgs_per_chat:
                keep = set(sorted(self.msgs[chat_id])[-max_msgs_per_chat:])
                for msg_id in list(self.msgs[chat_id]):
                    if msg_id not in keep:
                        del self.msgs[chat_id][msg_id]
                logging.warning(f'[bot_store]\tClearing messages for chat {chat_id}')
                cleared += 1
        if cleared:
            self.dirty = True
        return cleared

    def _last_active(self, chat_id: int):
        """Newest message date in a chat, for ranking. Empty chats sort last."""
        dates = [
            msg.date for msg in self.msgs[chat_id].values()
            if getattr(msg, 'date', None)
        ]
        return max(dates) if dates else None

    # --- background upkeep --------------------------------------------------

    def start_autosave(self):
        """
        Save on a timer instead of after every message, and prune while we are
        at it -- `clear()` used to be dead code, so the store only ever grew.
        """
        if self._task is None or self._task.done():
            self._task = asyncio.create_task(self._upkeep())
        return self._task

    def stop_autosave(self):
        if self._task and not self._task.done():
            self._task.cancel()
        self._task = None

    async def _upkeep(self):
        since_prune = 0
        while True:
            try:
                await asyncio.sleep(autosave_interval)
                since_prune += autosave_interval
                if since_prune >= prune_interval:
                    since_prune = 0
                    self.clear()
                if self.dirty:
                    self.save()
            except asyncio.CancelledError:
                return
            except Exception:
                logging.exception('[bot_store]\tUpkeep failed')

    # --- persistence --------------------------------------------------------

    def save(self):
        path = f'{msg_data_dir}/msg.p'
        tmp = f'{path}.tmp'
        try:
            with open(tmp, 'wb') as f:
                pickle.dump(self.msgs, f)
            os.replace(tmp, path)
            self.dirty = False
        except (OSError, pickle.PicklingError) as e:
            logging.error(f'[bot_store]\tCould not save: {e}')

    def load(self):
        path = f'{msg_data_dir}/msg.p'
        if not os.path.isfile(path):
            return
        try:
            with open(path, 'rb') as f:
                self.msgs = pickle.load(f)
        except Exception as e:
            # a store written by the pyrogram build cannot be read back
            logging.warning(f'[bot_store]\tDropping unreadable message store: {e}')
            self.msgs = {}
            return
        logging.info(f'[bot_store]\tLoaded {len(self.msgs)} chats from file')
