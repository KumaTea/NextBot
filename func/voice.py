import random
import aiohttp
import asyncio
import logging
from typing import Optional
from urllib.parse import urlencode
from bot.session import config
from bot.tools import get_file_link
from share.auth import ensure_auth
from telethon.tl.custom import Message
from common.info import max_voice_len, max_transcribe_len
from gpt.data import voice_tag, thinking_emojis, whisper_blacklist


def _transcribe_api() -> str:
    try:
        return config['ai']['transcribe']
    except KeyError:
        return 'http://10.3.3.6:12001/transcribe'


TRANSCRIBE_API = _transcribe_api()

# Whisper is loaded on demand on the other machine, so the first request after
# an idle period pays for the model load -- hence the generous total. Without
# any timeout at all a dead backend left the 👂 message on screen forever.
transcribe_timeout = aiohttp.ClientTimeout(total=1800, connect=10)

# What the bot will try to read an audio track out of, best first.
audio_kinds = ('voice', 'video_note', 'audio', 'video')
audio_mimes = ('audio/', 'video/')


def media_duration(media) -> int:
    """Seconds, from whichever attribute happens to carry it."""
    attributes = getattr(media, 'attributes', None) or []
    return int(next(
        (a.duration for a in attributes if getattr(a, 'duration', None)),
        0
    ))


def find_audio(message: Message):
    """Anything in a message that has sound in it, or None."""
    if not message:
        return None
    for kind in audio_kinds:
        media = getattr(message, kind, None)
        if media:
            return media
    # a file sent as a plain document still has a usable mime type
    document = getattr(message, 'document', None)
    if document and (document.mime_type or '').startswith(audio_mimes):
        return document
    return None


async def transcribe(file_link: str) -> str:
    # the link carries a token and a path, so it has to be encoded rather than
    # pasted straight into the query string
    query = urlencode({'url': file_link})
    async with aiohttp.ClientSession(timeout=transcribe_timeout) as session:
        async with session.get(f'{TRANSCRIBE_API}?{query}') as resp:
            body = await resp.text()
            if resp.status != 200:
                raise RuntimeError(f'transcribe returned {resp.status}: {body[:200]}')
            return body


async def transcribe_into(inform: Message, media) -> Message:
    """
    Transcribe `media`, reporting progress and result into `inform`.

    Shared by the automatic voice reaction and the explicit /transcribe
    command, so both report failures the same way.
    """
    try:
        file_link = await get_file_link(media)
    except Exception as e:
        logging.exception('[func_voice]\tCould not build a file link')
        # the Bot API refuses files over 20 MB, and says so
        return await inform.edit(f'拿不到这段音频捏（{e}）')

    try:
        text = await transcribe(file_link)
    except (asyncio.TimeoutError, TimeoutError):
        logging.warning('[func_voice]\tTranscription timed out')
        return await inform.edit('识别超时了捏')
    except Exception:
        logging.exception('[func_voice]\tTranscription failed')
        return await inform.edit('识别失败了捏')

    text = text.strip()
    if not text or any(word in text for word in whisper_blacklist):
        return await inform.edit('听不懂捏')

    seperator = '\n' if '\n' in text else ' '
    return await inform.edit(f'{text}{seperator}{voice_tag}')


async def react_voice(event) -> Optional[Message]:
    """
    Transcribe the voice message.
    :param event: The incoming voice or video note.
    :return: The message object.
    """
    message = event.message
    # `Message.voice` / `.video_note` hand back the Document itself
    media = message.voice or message.video_note
    if media_duration(media) > max_voice_len:
        return await message.reply('太长不听')

    inform = await message.reply(random.choice(thinking_emojis) + '👂')
    return await transcribe_into(inform, media)


@ensure_auth
async def command_transcribe(event) -> Optional[Message]:
    """
    /transcribe -- read out whatever audio the replied-to message carries.

    Unlike the automatic reaction this is asked for deliberately, so it accepts
    music and video files too, and allows a much longer recording.
    """
    reply = await event.get_reply_message()
    media = find_audio(reply) or find_audio(event.message)
    if not media:
        return await event.reply('请回复一条语音、音频或视频消息。')

    duration = media_duration(media)
    if duration > max_transcribe_len:
        minutes = max_transcribe_len // 60
        return await event.reply(f'太长了，最多 {minutes} 分钟。')

    inform = await event.reply(random.choice(thinking_emojis) + '👂')
    return await transcribe_into(inform, media)
