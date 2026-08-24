"""Mirroring @KumaSpace to X, with you in the loop.

Nothing is published without a button press. Deletion is watched three ways --
two events and a periodic sweep -- because `events.MessageDeleted` is not
guaranteed to reach a bot account, and the sweep is what actually guarantees a
deleted channel post takes its tweet with it.
"""

import asyncio
import logging
from telethon import Button, events
from telethon.tl.custom import Message

from x import client
from x import text as xtext
from x.store import sync_store
from x.bundle import Collector, Bundle
from x.config import (
    enabled, dry_run, link_back, approve_timeout,
    reconcile_interval, reconcile_batch, max_media,
)
from bot.tools import gen_uuid
from bot.session import bot
from common.info import sync_channel_id, sync_group_id, administrators


# Cap on what is worth pulling out of Telegram to hand to X.
max_media_bytes = 64 * 1024 * 1024

# channel post id -> the auto-forwarded copy in the discussion group, so the
# prompt can thread underneath the post it is asking about
forwarded: dict[int, int] = {}
forwarded_limit = 500

pending: dict[str, 'Pending'] = {}
collector: Collector = None
_tasks: list[asyncio.Task] = []


class Pending:
    def __init__(self, bundle: Bundle, prompt: Message, body: str):
        self.bundle = bundle
        self.prompt = prompt
        self.body = body
        self.timer: asyncio.Task = None


# --- helpers ----------------------------------------------------------------

async def alert(message: str):
    """Tell the admin something, in the discussion group."""
    try:
        await bot.send_message(sync_group_id, message, link_preview=False)
    except Exception:
        logging.exception('[x_sync]\tCould not deliver alert')


def _remember_forward(channel_msg_id: int, group_msg_id: int):
    forwarded[channel_msg_id] = group_msg_id
    if len(forwarded) > forwarded_limit:
        for key in sorted(forwarded)[:len(forwarded) - forwarded_limit]:
            forwarded.pop(key, None)


def _describe(bundle: Bundle, body: str) -> str:
    bits = [f'{xtext.weighted_len(body)}/280 计重']
    media = bundle.media_messages
    if media:
        bits.append(f'{min(len(media), max_media)} 个附件')
    if bundle.dropped_media:
        bits.append(f'超出 {bundle.dropped_media} 个将被丢弃')
    if dry_run:
        bits.append('DRY RUN')
    bits.append(f'{approve_timeout // 60} 分钟后自动取消')
    return ' · '.join(bits)


# --- the flow ---------------------------------------------------------------

async def on_channel_post(event):
    """A new channel post. Buffer it; the collector decides when it is done."""
    message = event.message
    if sync_store.was_seen(message.id):
        return
    if not (message.raw_text or message.media):
        return
    logging.info(f'[x_sync]\tChannel post {message.id}')
    collector.add(message)


async def on_bundle_ready(bundle: Bundle):
    """A post has settled: render it and ask."""
    body = xtext.render(
        bundle.text,
        message_id=min(bundle.ids),
        with_link=link_back,
    )
    if not body and not bundle.has_media:
        logging.info(f'[x_sync]\tBundle {bundle.ids} is empty, skipping')
        return

    sync_store.mark_seen(*bundle.ids)

    token = gen_uuid(8)
    prompt_text = (
        f'🕊 同步到 X？\n\n'
        f'{body or "(无正文)"}\n\n'
        f'—— {_describe(bundle, body)}'
    )
    buttons = [[
        Button.inline('✅ 同步', f'x_ok_{token}'.encode()),
        Button.inline('✖️ 取消', f'x_no_{token}'.encode()),
    ]]

    # thread under the auto-forwarded copy when it has already arrived
    reply_to = forwarded.get(min(bundle.ids))
    try:
        prompt = await bot.send_message(
            sync_group_id, prompt_text,
            buttons=buttons, reply_to=reply_to, link_preview=False,
        )
    except Exception:
        logging.exception(f'[x_sync]\tCould not post prompt for {bundle.ids}')
        return

    entry = Pending(bundle, prompt, body)
    pending[token] = entry
    entry.timer = asyncio.create_task(_expire(token))


async def _expire(token: str):
    try:
        await asyncio.sleep(approve_timeout)
    except asyncio.CancelledError:
        return
    entry = pending.pop(token, None)
    if entry is None:
        return
    logging.info(f'[x_sync]\tPrompt {token} expired')
    try:
        await entry.prompt.edit(
            f'⌛ 已超时，未同步\n\n{entry.body}', buttons=None, link_preview=False
        )
    except Exception:
        logging.exception('[x_sync]\tCould not expire prompt')


async def _collect_media(bundle: Bundle) -> list:
    blobs = []
    for message in bundle.media_messages[:max_media]:
        size = getattr(getattr(message, 'file', None), 'size', 0) or 0
        if size > max_media_bytes:
            logging.warning(
                f'[x_sync]\tSkipping media in {message.id}, {size} bytes is too large'
            )
            continue
        try:
            blob = await bot.download_media(message, file=bytes)
        except Exception:
            logging.exception(f'[x_sync]\tCould not download media from {message.id}')
            continue
        if blob:
            blobs.append(blob)
    return blobs


async def on_callback(event):
    """The sync / cancel buttons."""
    try:
        _, action, token = event.data.decode().split('_', 2)
    except (UnicodeDecodeError, ValueError):
        return await event.answer('无效的按钮', alert=True)

    if event.sender_id not in administrators:
        return await event.answer('不是你的别乱按！', alert=True)

    entry = pending.pop(token, None)
    if entry is None:
        return await event.answer('这条已经处理过了', alert=True)
    if entry.timer:
        entry.timer.cancel()

    if action == 'no':
        await event.answer('已取消')
        return await entry.prompt.edit(
            f'✖️ 已取消\n\n{entry.body}', buttons=None, link_preview=False
        )

    await event.answer('发布中…')
    await entry.prompt.edit(
        f'⏳ 发布中…\n\n{entry.body}', buttons=None, link_preview=False
    )

    media = await _collect_media(entry.bundle)
    try:
        tweet_id = await client.publish(entry.body, media)
    except client.XUnavailable as e:
        logging.error(f'[x_sync]\tPublish failed: {e}')
        return await entry.prompt.edit(
            f'❌ 同步失败：{e}\n\n{entry.body}', buttons=None, link_preview=False
        )

    sync_store.add(entry.bundle.ids, tweet_id, entry.body)
    url = client.status_url(tweet_id)
    return await entry.prompt.edit(
        f'✅ 已同步\n{url}\n\n{entry.body}', buttons=None, link_preview=False
    )


async def on_group_message(event):
    """
    Watch the linked group for the channel's auto-forwarded copies, so prompts
    thread under them and a group-side deletion can be traced back.
    """
    forward = event.message.forward
    if not forward:
        return
    # Forward copies the raw header's fields onto itself, so both of these are
    # plain attributes here.
    origin = getattr(forward, 'channel_post', None)
    if not origin:
        origin = getattr(forward, 'saved_from_msg_id', None)
    if origin:
        _remember_forward(origin, event.message.id)


# --- deletion ---------------------------------------------------------------

async def _unpublish(channel_msg_id: int, reason: str):
    record = sync_store.find(channel_msg_id)
    if record is None or record.get('deleted'):
        return
    tweet_id = record['tweet_id']
    logging.info(f'[x_sync]\t{reason}: removing tweet {tweet_id}')

    if await client.delete(tweet_id):
        sync_store.mark_deleted(channel_msg_id)
        await alert(
            f'🗑 频道消息已删除，对应推文已移除\n{client.status_url(tweet_id)}'
        )
    else:
        # the record stays live so the next sweep tries again
        await alert(f'⚠️ 推文删除失败，请手动删除\n{client.status_url(tweet_id)}')


async def on_deleted(event):
    """Channel or group deletions, whichever Telegram happens to tell us about."""
    chat_id = event.chat_id
    if chat_id == sync_channel_id:
        ids = list(event.deleted_ids)
        source = 'channel delete'
    elif chat_id == sync_group_id:
        # map the discussion-group copy back to the channel post
        back = {v: k for k, v in forwarded.items()}
        ids = [back[i] for i in event.deleted_ids if i in back]
        source = 'group delete'
    else:
        return

    for msg_id in ids:
        await _unpublish(msg_id, source)


async def reconcile():
    """
    The guarantee. Delete events may never reach a bot account, so every
    tracked post is re-fetched periodically; one that comes back as None is gone.
    """
    ids = sync_store.live_ids()
    if not ids:
        return

    missing = []
    for start in range(0, len(ids), reconcile_batch):
        batch = ids[start:start + reconcile_batch]
        try:
            messages = await bot.get_messages(sync_channel_id, ids=batch)
        except Exception:
            logging.exception('[x_sync]\tReconcile fetch failed')
            return
        missing.extend(
            msg_id for msg_id, message in zip(batch, messages) if message is None
        )

    if missing:
        logging.info(f'[x_sync]\tReconcile found {len(missing)} deleted: {missing}')
    for msg_id in missing:
        await _unpublish(msg_id, 'reconcile')


async def _reconcile_loop():
    while True:
        try:
            await asyncio.sleep(reconcile_interval)
            await reconcile()
        except asyncio.CancelledError:
            return
        except Exception:
            logging.exception('[x_sync]\tReconcile loop error')


# --- wiring -----------------------------------------------------------------

async def start() -> bool:
    """Bring the mirror up. Returns False if it is off or unusable."""
    global collector

    if not enabled:
        logging.info('[x_sync]\tMirror disabled by config')
        return False

    if not await client.init():
        await alert(
            '⚠️ X 同步未能启动：cookies 缺失/失效，或 twikit 不可用。\n'
            '请更新 data/x/cookies.json 后重启。'
        )
        return False

    collector = Collector(on_bundle_ready)

    bot.add_event_handler(on_channel_post, events.NewMessage(
        func=lambda e: e.chat_id == sync_channel_id
    ))
    bot.add_event_handler(on_group_message, events.NewMessage(
        func=lambda e: e.chat_id == sync_group_id
    ))
    bot.add_event_handler(on_deleted, events.MessageDeleted(
        func=lambda e: e.chat_id in (sync_channel_id, sync_group_id)
    ))

    _tasks.append(asyncio.create_task(_reconcile_loop()))
    logging.info(f'[x_sync]\tMirror active{" (dry run)" if dry_run else ""}')
    return True


def stop():
    for task in _tasks:
        task.cancel()
    _tasks.clear()
    if collector:
        collector.cancel()
    for entry in pending.values():
        if entry.timer:
            entry.timer.cancel()
    pending.clear()
