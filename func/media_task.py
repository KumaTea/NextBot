"""Handing work to the media bot on the router.

`ocr` and `cap` were byte-for-byte the same but for the payload, including the
same unbounded wait, so the queueing lives here once.
"""

import os
import asyncio
import logging
from time import monotonic
from common.data import TEMP_DIR, MEDIA_BOT_CMD


TASK_FILE = f'{TEMP_DIR}/task.txt'
STATUS_FILE = f'{TEMP_DIR}/media.run'

# The media bot runs on underpowered hardware, so slow is expected -- but the
# wait used to have no end at all, and a stale lock file hung the handler
# for as long as the bot stayed up.
wait_timeout = 300  # seconds


async def wait_for_slot() -> bool:
    """Wait for any running media task to finish. False if it never does."""
    deadline = monotonic() + wait_timeout
    while os.path.isfile(STATUS_FILE):
        if monotonic() > deadline:
            logging.warning(
                f'[media_task]\t{STATUS_FILE} still present after '
                f'{wait_timeout}s, giving up'
            )
            return False
        await asyncio.sleep(1)
    return True


async def queue(*fields) -> bool:
    """Append a task and kick the media bot off. False if it could not start."""
    try:
        with open(TASK_FILE, 'a') as f:
            f.write(','.join(map(str, fields)) + '\n')
    except OSError:
        logging.exception('[media_task]\tCould not queue the task')
        return False

    if not await wait_for_slot():
        return False
    await asyncio.create_subprocess_shell(MEDIA_BOT_CMD)
    return True
