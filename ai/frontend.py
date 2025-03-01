import aiohttp
import asyncio
from aiohttp import web


async def check_program_running(program: str) -> bool:
    # command = 'ps aux | grep uvicorn | grep -v grep'
    command = f'ps -e | grep {program}'
    process = await asyncio.create_subprocess_shell(
        command,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    stdout, stderr = await process.communicate()
    return program in stdout.decode()


async def wait_for_backend():
    url = 'http://10.3.3.6:12000/getStatus'
    timeout_ms = 1000

    if not await check_program_running('uvicorn'):
        await asyncio.create_subprocess_shell(
            '/bin/bash /home/kuma/NextBot/ai/run-backend.sh'
        )

    while True:
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=timeout_ms / 1000)) as session:
                async with session.get(url) as resp:
                    if resp.status == 200:
                        return True
        # except TimeoutError:
        except:
            pass


# take a url and forward it to localhost:12000
async def transcribe(request):
    await wait_for_backend()
    url = request.query.get('url')
    if not url:
        return web.Response(text='url parameter is required', status=400)
    async with aiohttp.ClientSession() as session:
        async with session.get(
            f'http://10.3.3.6:12000/transcribe?url={url}'
        ) as resp:
            return web.Response(text=await resp.text())


app = web.Application()
app.add_routes([web.get('/transcribe', transcribe)])


if __name__ == '__main__':
    web.run_app(app, host='0.0.0.0', port=12001)
