from v2t.base import *
from v2t.whisper import model_storage


IDLE_SECONDS = 60 * 10  # minutes

_task = None


async def exit_after_idle():
    while (to_sleep := IDLE_SECONDS - (datetime.now() - model_storage.run_at).total_seconds()) > 0:
        # still need to sleep
        await asyncio.sleep(to_sleep)

    logging.info('Idle time reached. Quitting...')
    try:
        sys.exit(0)
    except SystemExit:
        # SystemExit raised inside a task only kills the task; uvicorn keeps
        # serving, so the process is signalled instead
        import os
        import signal
        pid = os.getpid()
        logging.info(f'Exiting with os.kill: {pid}')
        os.kill(pid, signal.SIGINT)


def create_idle_task():
    """
    Start the idle-exit watchdog, at most once.

    This is called at import time, which only happens to work because uvicorn
    imports the app from inside its event loop. When there is no loop yet the
    start is left to the app's lifespan instead of raising.
    """
    global _task
    if _task is not None and not _task.done():
        return _task
    try:
        _task = asyncio.create_task(exit_after_idle())
    except RuntimeError:
        logging.info('No running event loop yet; the watchdog starts with the app')
        _task = None
    return _task
