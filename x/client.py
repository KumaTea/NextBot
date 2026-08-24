"""The one and only way this bot talks to X.

There is no official-API fallback and no second transport by design: if this
path fails for any reason the item is abandoned and you get told about it,
rather than the bot quietly trying something else.

Authentication is cookies only -- X removed the password flow -- so
`data/x/cookies.json` has to be refreshed by hand now and then. Every failure
mode below is reported with the sentence you would need to act on.
"""

import os
import logging

from x.config import cookies_file, dry_run
from common.info import x_user_id, x_username


class XUnavailable(Exception):
    """X cannot be used right now. The message is written to be shown to you."""


_client = None
_ready = False

# twikit is imported inside init(): a broken dependency must not stop the bot
# from starting, it should just switch the mirror off.
_errors = None


def status_url(tweet_id) -> str:
    return f'https://x.com/{x_username}/status/{tweet_id}'


def _degrade(reason: str) -> bool:
    """
    Report a startup failure.

    In a dry run the mirror still comes up, so the Telegram half stays
    testable without working X access; otherwise the mirror stays off.
    """
    global _ready
    if dry_run:
        logging.warning(f'[x_client]\t{reason} -- continuing anyway, dry run')
        _ready = True
        return True
    logging.error(f'[x_client]\t{reason}, mirror disabled')
    return False


async def init() -> bool:
    """
    Bring the client up. Returns False -- and never raises -- if X is not
    usable, so a dead mirror cannot take the rest of the bot down with it.

    The cookies are checked even in a dry run, so startup tells you whether
    they are still good *before* you turn publishing on.
    """
    global _client, _ready, _errors

    if _ready:
        return True
    if dry_run:
        logging.warning('[x_client]\tDry run: nothing will be published to X')

    try:
        from twikit import Client
        from twikit import errors
    except Exception as e:
        return _degrade(f'twikit unavailable: {e!r}')
    _errors = errors

    if not os.path.isfile(cookies_file):
        return _degrade(f'no cookies at {cookies_file}')

    client = Client('en-US')
    try:
        client.load_cookies(cookies_file)
    except Exception as e:
        return _degrade(f'cookies unreadable: {e!r}')

    # Publishing to the wrong account is worse than not publishing, so confirm
    # whose cookies these actually are before anything can be sent.
    try:
        who = int(await client.user_id())
    except Exception as e:
        return _degrade(f'cookies rejected by X: {e!r}')

    if who != x_user_id:
        return _degrade(
            f'cookies belong to {who}, expected {x_user_id} (@{x_username})'
        )

    _client, _ready = client, True
    logging.info(f'[x_client]\tReady as @{x_username} ({who})')
    return True


def _translate(e: Exception) -> XUnavailable:
    """Turn a twikit error into something worth reading in Telegram."""
    if _errors is None:
        return XUnavailable(f'{type(e).__name__}: {e}')
    if isinstance(e, (_errors.Unauthorized, _errors.Forbidden)):
        return XUnavailable('Cookies 已失效，请重新导出 cookies.json')
    if isinstance(e, _errors.AccountLocked):
        return XUnavailable('X 账号被锁定，需要手动解锁')
    if isinstance(e, _errors.AccountSuspended):
        return XUnavailable('X 账号已被封禁')
    if isinstance(e, _errors.TooManyRequests):
        return XUnavailable('X 限流，请稍后重试')
    if isinstance(e, _errors.DuplicateTweet):
        return XUnavailable('X 拒绝重复内容')
    if isinstance(e, _errors.InvalidMedia):
        return XUnavailable('X 拒绝了这个附件')
    return XUnavailable(f'{type(e).__name__}: {e}')


async def publish(text: str, media: list = None) -> str:
    """
    Post to X and hand back the tweet id.

    Raises `XUnavailable` on any failure -- callers report it and give up.
    """
    if dry_run:
        logging.warning(
            f'[x_client]\tDRY RUN, would post '
            f'({len(media or ())} media): {text!r}'
        )
        return 'dryrun'

    if not _ready or _client is None:
        raise XUnavailable('X 客户端未就绪')

    media_ids = []
    for index, blob in enumerate(media or ()):
        try:
            media_ids.append(await _client.upload_media(blob))
        except Exception as e:
            logging.exception(f'[x_client]\tMedia {index} failed to upload')
            raise _translate(e) from e

    try:
        tweet = await _client.create_tweet(text=text, media_ids=media_ids or None)
    except Exception as e:
        logging.exception('[x_client]\tPublish failed')
        raise _translate(e) from e

    tweet_id = str(getattr(tweet, 'id', '') or '')
    if not tweet_id:
        raise XUnavailable('X 未返回 tweet id')
    logging.info(f'[x_client]\tPublished {status_url(tweet_id)}')
    return tweet_id


async def delete(tweet_id: str) -> bool:
    """
    Remove a tweet. Returns False instead of raising, because the caller's
    answer to a failed delete is always the same: tell you to do it by hand.
    """
    if dry_run:
        logging.warning(f'[x_client]\tDRY RUN, would delete {tweet_id}')
        return True

    if not _ready or _client is None:
        logging.error('[x_client]\tCannot delete, client not ready')
        return False

    try:
        await _client.delete_tweet(str(tweet_id))
    except Exception as e:
        # already gone is a success as far as we are concerned
        if _errors is not None and isinstance(e, _errors.NotFound):
            logging.info(f'[x_client]\tTweet {tweet_id} was already gone')
            return True
        logging.exception(f'[x_client]\tDelete of {tweet_id} failed')
        return False

    logging.info(f'[x_client]\tDeleted {tweet_id}')
    return True
