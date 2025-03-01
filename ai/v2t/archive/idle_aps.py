from v2t.base import *
from apscheduler.schedulers.asyncio import AsyncIOScheduler


IDLE_SECONDS = 60 * 5  # 5 minutes

scheduler = AsyncIOScheduler()


def exit_after_idle():
    logging.info('Idle time reached. Quitting...')
    sys.exit(0)


exit_time = datetime.now() + timedelta(seconds=IDLE_SECONDS)

scheduler.add_job(
    exit_after_idle,
    'date',
    run_date=exit_time,
    id='exit_after_idle',
    replace_existing=True,
)
