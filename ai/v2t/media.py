import os
import uuid
import aiohttp
import logging


TMP_PATH = '/dev/shm/v2t'

# 1 KiB reads made a long download needlessly slow.
DOWNLOAD_CHUNK = 64 * 1024
DOWNLOAD_TIMEOUT = aiohttp.ClientTimeout(total=600, connect=15)
# The endpoint takes any URL and TMP_PATH is a RAM disk, so an unbounded
# download is a way to fill memory from the outside. Well above anything
# Telegram will hand out.
MAX_DOWNLOAD = 512 * 1024 * 1024  # bytes

# Telegram does not care, but plenty of hosts reject the default aiohttp
# agent outright (Wikimedia answers 403), and the endpoint takes any URL.
DOWNLOAD_HEADERS = {
    'User-Agent': (
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 '
        '(KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36'
    )
}


def _extension(url: str, headers) -> str:
    """
    A safe file extension for the download.

    PyAV sniffs the container from its contents rather than the name, so this
    is no longer load-bearing -- but a suffix keeps scratch files readable in
    a log, and only a short alphanumeric one is accepted.
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
    filename = ''

    try:
        async with aiohttp.ClientSession(timeout=DOWNLOAD_TIMEOUT) as session:
            async with session.get(url, headers=DOWNLOAD_HEADERS) as resp:
                resp.raise_for_status()
                filename = base + _extension(url, resp.headers)
                written = 0
                with open(filename, 'wb') as f:
                    async for chunk in resp.content.iter_chunked(DOWNLOAD_CHUNK):
                        written += len(chunk)
                        if written > MAX_DOWNLOAD:
                            raise RuntimeError(
                                f'download is over {MAX_DOWNLOAD // (1024 * 1024)} MiB'
                            )
                        f.write(chunk)
    except Exception:
        # the caller only cleans up paths it was handed back, so a download
        # that died part way has to take its own half-written file with it
        if filename and os.path.exists(filename):
            os.remove(filename)
        raise
    return filename
