from v2t.base import logging, asyncio
from v2t.whisper import whisper_transcribe

logging.info('Loading starlette')

# https://huggingface.co/docs/transformers/en/pipeline_webserver

from starlette.routing import Route
from starlette.applications import Starlette
from starlette.responses import JSONResponse


async def get_status(request):
    return JSONResponse({'status': 'ok'})


async def transcribe(request):
    # payload = await request.body()
    # string = payload.decode()
    req_json = await request.json()
    url = req_json.get('url')
    file_path = req_json.get('file_path')
    file_data = req_json.get('file_data')
    response_q = asyncio.Queue()
    await request.app.model_queue.put((url, file_path, file_data, response_q))
    output = await response_q.get()
    return JSONResponse(output)


async def server_loop(q):
    while True:
        (url, file_path, file_data, response_q) = await q.get()
        out = await whisper_transcribe(url, file_path, file_data)
        await response_q.put(out)


app = Starlette(
    routes=[
        Route("/", get_status, methods=["GET"]),
        Route("/GetStatus", get_status, methods=["GET"]),
    ],
)


@app.on_event('startup')
async def startup_event():
    q = asyncio.Queue()
    app.model_queue = q
    asyncio.create_task(server_loop(q))
