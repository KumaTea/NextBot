from v2t.base import logging, asyncio
from v2t.whisper import whisper_transcribe

logging.info('Loading starlette')

# https://huggingface.co/docs/transformers/en/pipeline_webserver

from starlette.routing import Route
from starlette.requests import Request
from starlette.applications import Starlette
from starlette.responses import JSONResponse


async def get_status():
    return JSONResponse({'status': 'ok'})


async def transcribe(request: Request):
    if request.method == 'GET':
        url = request.query_params.get('url')
        file_path = request.query_params.get('file_path')
        file_data = request.query_params.get('file_data')
    else:  # POST
        data = await request.json()  # or await request.form()
        url = data.get('url')
        file_path = data.get('file_path')
        file_data = data.get('file_data')

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
        Route('/', get_status, methods=['GET']),
        Route('/getStatus', get_status, methods=['GET']),

        Route('/transcribe', transcribe, methods=['GET', 'POST']),
    ],
)


@app.on_event('startup')
async def startup_event():
    q = asyncio.Queue()
    app.model_queue = q
    asyncio.create_task(server_loop(q))
