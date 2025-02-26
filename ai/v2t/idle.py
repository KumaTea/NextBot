from v2t.base import *
from v2t.whisper import model_storage


IDLE_SECONDS = 60 * 5  # 5 minutes


async def exit_after_idle():
    while (to_sleep := IDLE_SECONDS - (datetime.now() - model_storage.run_at).total_seconds()) > 0:
        # still need to sleep
        await asyncio.sleep(to_sleep)

    logging.info('Idle time reached. Quitting...')
    try:
        sys.exit(0)
    except SystemExit:
        import os
        import signal
        pid = os.getpid()
        logging.info(f'Exiting with os.kill: {pid}')
        os.kill(pid, signal.SIGINT)


def create_idle_task():
    asyncio.create_task(exit_after_idle())
