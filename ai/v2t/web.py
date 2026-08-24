from v2t.base import logging, asyncio
from v2t.whisper import whisper_transcribe
from v2t.idle import create_idle_task

logging.info('Loading starlette')

# https://huggingface.co/docs/transformers/en/pipeline_webserver

from contextlib import asynccontextmanager
from starlette.routing import Route
from starlette.requests import Request
from starlette.applications import Starlette
from starlette.responses import JSONResponse, PlainTextResponse


async def get_status(request):
    return JSONResponse({'status': 'ok'})


async def transcribe(request: Request):
    if request.method == 'GET':
        params = request.query_params
    else:  # POST
        params = await request.json()  # or await request.form()

    url = params.get('url')
    file_path = params.get('file_path')
    file_data = params.get('file_data')
    if not (url or file_path or file_data):
        return PlainTextResponse('nothing to transcribe', status_code=400)

    response_q = asyncio.Queue()
    await request.app.state.queue.put((url, file_path, file_data, response_q))
    ok, output = await response_q.get()
    if not ok:
        # a failure has to read as a failure: this used to come back as 200
        # with the exception text, which the bot then published as speech
        return PlainTextResponse(output, status_code=500)
    return PlainTextResponse(output)


async def server_loop(queue):
    """
    One transcription at a time -- the model is not reentrant and there is only
    so much memory. The body is guarded because a loop that dies on one bad
    request would hang every request after it.
    """
    while True:
        url, file_path, file_data, response_q = await queue.get()
        try:
            out = await whisper_transcribe(url, file_path, file_data)
            await response_q.put((True, out))
        except asyncio.CancelledError:
            raise
        except Exception as e:
            logging.exception('Transcription failed')
            await response_q.put((False, f'{type(e).__name__}: {e}'))


@asynccontextmanager
async def lifespan(app):
    # replaces @app.on_event('startup'), removed in current starlette
    app.state.queue = asyncio.Queue()
    worker = asyncio.create_task(server_loop(app.state.queue))
    # a no-op if main.py already managed to start it at import time
    create_idle_task()
    try:
        yield
    finally:
        worker.cancel()


app = Starlette(
    routes=[
        Route('/', get_status, methods=['GET']),
        Route('/getStatus', get_status, methods=['GET']),

        Route('/transcribe', transcribe, methods=['GET', 'POST']),
    ],
    lifespan=lifespan,
)
