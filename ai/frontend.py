"""Front door for the transcription backend.

The backend holds a multi-gigabyte whisper model, so it is started on demand
and exits again once idle. This process stays up and is what the bot talks to.
"""

import asyncio
import logging
import aiohttp
from aiohttp import web


logging.basicConfig(
    format='%(asctime)s %(levelname)-8s %(message)s',
    level=logging.INFO,
    datefmt='%Y-%m-%d %H:%M:%S')

BACKEND_HOST = '10.3.3.6'
BACKEND_PORT = 12000
BACKEND_URL = f'http://{BACKEND_HOST}:{BACKEND_PORT}'

RUN_BACKEND = '/bin/bash /home/kuma/NextBot/ai/run-backend.sh'

LISTEN_PORT = 12001

# Loading the model takes a while on CPU, so first use after an idle period is
# slow -- but not unbounded, which is what it used to be.
STARTUP_TIMEOUT = 300  # seconds
POLL_INTERVAL = 2  # seconds
PROBE_TIMEOUT = 2  # seconds
TRANSCRIBE_TIMEOUT = aiohttp.ClientTimeout(total=1800, connect=10)

# Only one caller may decide to start the backend. Without this, two requests
# arriving together both start one, and the loser burns a full model load
# before dying on the already-bound port.
spawn_lock = asyncio.Lock()


async def backend_listening() -> bool:
    """
    Is anything bound to the backend port?

    This replaces a `ps -e | grep uvicorn`, which never matched: uvicorn is a
    shebang script, so `ps -e` reports the process as `python3` and the check
    always concluded that nothing was running.
    """
    try:
        _, writer = await asyncio.wait_for(
            asyncio.open_connection(BACKEND_HOST, BACKEND_PORT),
            timeout=PROBE_TIMEOUT,
        )
    except (OSError, asyncio.TimeoutError, TimeoutError):
        return False
    writer.close()
    try:
        await writer.wait_closed()
    except OSError:
        pass
    return True


async def backend_ready() -> bool:
    """Listening is not enough -- the model has to be loaded and serving."""
    timeout = aiohttp.ClientTimeout(total=PROBE_TIMEOUT)
    try:
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(f'{BACKEND_URL}/getStatus') as resp:
                return resp.status == 200
    except (aiohttp.ClientError, asyncio.TimeoutError, TimeoutError, OSError):
        return False


async def _reap(process):
    """run-backend.sh backgrounds uvicorn and returns; don't leave a zombie."""
    try:
        await process.wait()
    except Exception:
        logging.exception('Could not reap the launcher')


async def ensure_backend() -> bool:
    """Start the backend if needed and wait for it to serve."""
    if await backend_ready():
        return True

    async with spawn_lock:
        # another caller may have started it while we waited for the lock
        if await backend_ready():
            return True
        if not await backend_listening():
            logging.info('Backend is not up, starting it')
            process = await asyncio.create_subprocess_shell(RUN_BACKEND)
            asyncio.create_task(_reap(process))

        deadline = asyncio.get_running_loop().time() + STARTUP_TIMEOUT
        while asyncio.get_running_loop().time() < deadline:
            if await backend_ready():
                return True
            await asyncio.sleep(POLL_INTERVAL)

    logging.error(f'Backend did not come up within {STARTUP_TIMEOUT}s')
    return False


async def transcribe(request):
    url = request.query.get('url')
    if not url:
        return web.Response(text='url parameter is required', status=400)

    if not await ensure_backend():
        return web.Response(text='transcription backend unavailable', status=503)

    try:
        async with aiohttp.ClientSession(timeout=TRANSCRIBE_TIMEOUT) as session:
            # params= so the link is encoded rather than pasted into the query
            async with session.get(
                f'{BACKEND_URL}/transcribe', params={'url': url}
            ) as resp:
                # the status is passed through, so a failure upstream reads as
                # a failure here instead of arriving as transcribed text
                return web.Response(text=await resp.text(), status=resp.status)
    except (aiohttp.ClientError, asyncio.TimeoutError, TimeoutError, OSError) as e:
        logging.error(f'Backend request failed: {e}')
        return web.Response(text=f'backend error: {e}', status=502)


async def status(request):
    return web.json_response({'status': 'ok', 'backend': await backend_ready()})


app = web.Application()
app.add_routes([
    web.get('/transcribe', transcribe),
    web.get('/getStatus', status),
])


if __name__ == '__main__':
    web.run_app(app, host='0.0.0.0', port=LISTEN_PORT)
