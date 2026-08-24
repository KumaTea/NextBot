"""Collecting the messages that together make up one tweet.

Telegram splits what you think of as a single post across several messages: an
album arrives one message per image, and a caption written afterwards is its
own message again. Prompting per Telegram message would ask three times about
one post, so messages are buffered here first.

Merging is deliberately narrow -- an album, or media still waiting for its
caption -- so two unrelated posts made a minute apart never end up as one tweet.
"""

import asyncio
import logging
from time import monotonic
from telethon.tl.custom import Message

from x.config import album_debounce, text_debounce, text_wait, max_media


class Bundle:
    def __init__(self, message: Message):
        self.messages: list[Message] = []
        self.grouped_id = message.grouped_id
        self.touched = monotonic()
        # set when something arrives that the waiting loop should react to
        self.wake = asyncio.Event()
        self.task: asyncio.Task | None = None
        self.absorb(message)

    def absorb(self, message: Message):
        self.messages.append(message)
        self.touched = monotonic()
        self.wake.set()

    @property
    def ids(self) -> list[int]:
        return sorted(m.id for m in self.messages)

    @property
    def text(self) -> str:
        """The first non-empty caption or body in the bundle."""
        for message in self.messages:
            if message.raw_text and message.raw_text.strip():
                return message.raw_text.strip()
        return ''

    @property
    def media_messages(self) -> list[Message]:
        return [m for m in self.messages if m.media and not m.web_preview]

    @property
    def has_media(self) -> bool:
        return bool(self.media_messages)

    @property
    def dropped_media(self) -> int:
        """How many attachments will not fit in a tweet."""
        return max(0, len(self.media_messages) - max_media)


def _is_text_only(message: Message) -> bool:
    has_text = bool(message.raw_text and message.raw_text.strip())
    return has_text and not (message.media and not message.web_preview)


class Collector:
    """
    Buffers channel posts and hands finished bundles to `on_ready`.

    Channel posts arrive in order, so only one bundle is ever open.
    """

    def __init__(self, on_ready):
        self.on_ready = on_ready
        self.open: Bundle | None = None

    def add(self, message: Message):
        current = self.open

        if current is not None:
            same_album = (
                message.grouped_id is not None
                and message.grouped_id == current.grouped_id
            )
            awaiting_caption = (
                current.has_media
                and not current.text
                and _is_text_only(message)
            )
            if same_album or awaiting_caption:
                current.absorb(message)
                logging.info(
                    f'[x_bundle]\tMerged {message.id} into bundle {current.ids}'
                )
                return
            # unrelated: the open bundle is finished, whatever it was waiting for
            self._close_now(current)

        self.open = Bundle(message)
        self.open.task = asyncio.create_task(self._wait(self.open))

    def _close_now(self, bundle: Bundle):
        """Stop waiting and let the bundle go out as it stands."""
        if bundle.task and not bundle.task.done():
            bundle.task.cancel()
        if self.open is bundle:
            self.open = None
        asyncio.create_task(self._deliver(bundle))

    async def _rest(self, bundle: Bundle, seconds: float) -> bool:
        """
        Sleep, but come back early if the bundle changed.
        Returns True if something arrived while waiting.
        """
        bundle.wake.clear()
        try:
            await asyncio.wait_for(bundle.wake.wait(), timeout=seconds)
            return True
        except (asyncio.TimeoutError, TimeoutError):
            return False

    async def _wait(self, bundle: Bundle):
        try:
            # Phase 1: let the rest of an album land. Each new member pushes
            # the deadline out again.
            settle = album_debounce if bundle.grouped_id else text_debounce
            while True:
                remaining = settle - (monotonic() - bundle.touched)
                if remaining <= 0:
                    break
                await self._rest(bundle, remaining)

            # Phase 2: media with no caption yet gets a while to acquire one.
            if bundle.has_media and not bundle.text:
                logging.info(
                    f'[x_bundle]\tBundle {bundle.ids} has no caption, '
                    f'waiting up to {text_wait}s'
                )
                deadline = monotonic() + text_wait
                while not bundle.text:
                    remaining = deadline - monotonic()
                    if remaining <= 0:
                        break
                    await self._rest(bundle, remaining)
        except asyncio.CancelledError:
            return

        if self.open is bundle:
            self.open = None
        await self._deliver(bundle)

    async def _deliver(self, bundle: Bundle):
        try:
            await self.on_ready(bundle)
        except Exception:
            logging.exception(f'[x_bundle]\tHandling bundle {bundle.ids} failed')

    def cancel(self):
        """Drop anything still buffered, on shutdown."""
        if self.open and self.open.task and not self.open.task.done():
            self.open.task.cancel()
        self.open = None
