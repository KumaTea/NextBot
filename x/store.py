"""What has been mirrored, and what is still waiting.

Deliberately JSON rather than a pickle: this file is the only record of which
tweet belongs to which channel post, so it needs to stay readable and to
survive a change of shape. `data/msg/msg.p` already had to be taught to throw
itself away when the pickle stopped loading -- this one should never need that.
"""

import os
import json
import logging
from datetime import datetime, timezone

from x.config import store_file, x_data_dir


# A post is remembered under the lowest message id of its bundle. Albums and a
# trailing caption arrive as several messages but become one tweet, so every
# member id also points back at that record.
version = 1
seen_limit = 2000  # ids remembered purely to avoid re-prompting after a restart


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec='seconds')


class SyncStore:
    def __init__(self):
        self.posts: dict[int, dict] = {}
        self.seen: list[int] = []
        self._by_member: dict[int, int] = {}
        self.load()

    # --- lookup -------------------------------------------------------------

    def reindex(self):
        self._by_member = {
            member: primary
            for primary, record in self.posts.items()
            for member in record.get('ids', [primary])
        }

    def find(self, msg_id: int) -> dict | None:
        """The record a channel message belongs to, by any of its message ids."""
        primary = self._by_member.get(msg_id)
        return self.posts.get(primary) if primary is not None else None

    def live_ids(self) -> list[int]:
        """Every message id still backing a published tweet."""
        return sorted(
            member
            for record in self.posts.values()
            if not record.get('deleted')
            for member in record.get('ids', ())
        )

    # --- mutation -----------------------------------------------------------

    def add(self, ids: list[int], tweet_id: str, text: str):
        primary = min(ids)
        self.posts[primary] = {
            'ids': sorted(ids),
            'tweet_id': str(tweet_id),
            'text': text,
            'at': _now(),
            'deleted': False,
        }
        self.reindex()
        self.save()

    def mark_deleted(self, msg_id: int):
        record = self.find(msg_id)
        if record and not record.get('deleted'):
            record['deleted'] = True
            record['deleted_at'] = _now()
            self.save()
        return record

    def mark_seen(self, *msg_ids: int):
        """
        Remember that a post has already been offered for approval, so a
        restart does not put the same prompt up twice.
        """
        added = [i for i in msg_ids if i not in self.seen]
        if not added:
            return
        self.seen.extend(added)
        if len(self.seen) > seen_limit:
            self.seen = self.seen[-seen_limit:]
        self.save()

    def was_seen(self, msg_id: int) -> bool:
        return msg_id in self.seen or msg_id in self._by_member

    # --- persistence --------------------------------------------------------

    def save(self):
        os.makedirs(x_data_dir, exist_ok=True)
        payload = {
            'version': version,
            'posts': {str(k): v for k, v in self.posts.items()},
            'seen': self.seen[-seen_limit:],
        }
        # write beside the target, then swap: a crash mid-write cannot leave a
        # half-written map of published tweets behind
        tmp = f'{store_file}.tmp'
        try:
            with open(tmp, 'w', encoding='utf-8') as f:
                json.dump(payload, f, ensure_ascii=False, indent=1)
            os.replace(tmp, store_file)
        except OSError as e:
            logging.error(f'[x_store]\tCould not save: {e}')

    def load(self):
        if not os.path.isfile(store_file):
            return
        try:
            with open(store_file, encoding='utf-8') as f:
                payload = json.load(f)
            self.posts = {int(k): v for k, v in payload.get('posts', {}).items()}
            self.seen = list(payload.get('seen', ()))
        except (OSError, ValueError) as e:
            logging.error(f'[x_store]\tUnreadable store, starting empty: {e}')
            self.posts, self.seen = {}, []
        self.reindex()
        live = sum(1 for r in self.posts.values() if not r.get('deleted'))
        logging.info(f'[x_store]\tLoaded {len(self.posts)} posts ({live} live)')


sync_store = SyncStore()
