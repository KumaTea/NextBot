import os
import uuid
import aiohttp
import asyncio
import logging


FFMPEG_BIN = '/usr/bin/ffmpeg'
FFPROBE_BIN = '/usr/bin/ffprobe'
TMP_PATH = '/dev/shm/v2t'

# 1 KiB reads made a long download needlessly slow.
DOWNLOAD_CHUNK = 64 * 1024
DOWNLOAD_TIMEOUT = aiohttp.ClientTimeout(total=600, connect=15)
PROCESS_TIMEOUT = 300  # seconds

# Telegram does not care, but plenty of hosts reject the default aiohttp
# agent outright (Wikimedia answers 403), and the endpoint takes any URL.
DOWNLOAD_HEADERS = {
    'User-Agent': (
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 '
        '(KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36'
    )
}


async def run(*argv) -> str:
    """
    Run a command from an argv list.

    Never through a shell: these commands take a path built partly from a
    remote URL, and a shell would happily read metacharacters in it.
    """
    proc = await asyncio.create_subprocess_exec(
        *argv,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    try:
        stdout, stderr = await asyncio.wait_for(
            proc.communicate(), timeout=PROCESS_TIMEOUT
        )
    except (asyncio.TimeoutError, TimeoutError):
        proc.kill()
        await proc.wait()
        raise RuntimeError(f'{os.path.basename(argv[0])} timed out')

    if proc.returncode != 0:
        detail = stderr.decode(errors='replace').strip()[-200:]
        raise RuntimeError(f'{os.path.basename(argv[0])} failed: {detail}')
    return stdout.decode(errors='replace').strip()


def _extension(url: str, headers) -> str:
    """
    A safe file extension for the download.

    Whatever comes back here ends up in a path passed to ffmpeg, so only a
    short alphanumeric suffix is accepted.
    """
    name = url.split('/')[-1].split('?')[0]
    ext = name.rsplit('.', 1)[-1] if '.' in name else ''

    if not ext:
        disposition = headers.get('Content-Disposition', '')
        if 'filename=' in disposition:
            filename = disposition.split('filename=')[-1].strip('"; ')
            ext = filename.rsplit('.', 1)[-1] if '.' in filename else ''

    if ext and len(ext) <= 8 and ext.isalnum():
        return '.' + ext.lower()
    return ''


async def download(url: str) -> str:
    """Fetch a URL into the scratch directory and return the path."""
    os.makedirs(TMP_PATH, exist_ok=True)
    base = os.path.join(TMP_PATH, str(uuid.uuid4()))

    async with aiohttp.ClientSession(timeout=DOWNLOAD_TIMEOUT) as session:
        async with session.get(url, headers=DOWNLOAD_HEADERS) as resp:
            resp.raise_for_status()
            filename = base + _extension(url, resp.headers)
            with open(filename, 'wb') as f:
                async for chunk in resp.content.iter_chunked(DOWNLOAD_CHUNK):
                    f.write(chunk)
    return filename


async def is_video(path: str) -> bool:
    try:
        out = await run(
            FFPROBE_BIN, '-v', 'error',
            '-select_streams', 'v:0',
            '-show_entries', 'stream=codec_type',
            '-of', 'default=noprint_wrappers=1:nokey=1',
            path,
        )
    except RuntimeError as e:
        logging.warning(f'Could not probe {path}: {e}')
        return False
    return out == 'video'


async def extract_audio(video_path: str) -> str:
    """Pull the audio track out of a video, returning the new file's path."""
    audio_path = os.path.join(TMP_PATH, f'{uuid.uuid4()}.aac')
    await run(
        FFMPEG_BIN, '-nostdin', '-y',
        '-i', video_path,
        '-vn', '-acodec', 'aac', '-strict', '-2',
        audio_path,
    )
    return audio_path


async def get_audio_length(path: str) -> int:
    out = await run(
        FFPROBE_BIN, '-v', 'error',
        '-show_entries', 'format=duration',
        '-of', 'default=noprint_wrappers=1:nokey=1',
        path,
    )
    try:
        return int(float(out))
    except ValueError:
        logging.warning(f'Could not read a duration from {out!r}')
        return 0
