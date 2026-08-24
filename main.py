import os
import asyncio

if os.name == 'posix':
    # A speed-up, not a requirement: an image without it should still run.
    try:
        import uvloop
        uvloop.install()
    except ImportError:
        pass

from bot.starting import starting
from bot.stopping import stopping
from bot.session import bot, logging, BOT_TOKEN


async def main():
    await bot.start(bot_token=BOT_TOKEN)
    await starting()
    try:
        await bot.run_until_disconnected()
    finally:
        # while the loop is still alive, so background tasks can be cancelled
        stopping()
        await bot.disconnect()


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info('[main]\tInterrupted')
    except SystemExit:
        logging.info('[main]\tExit requested')
    except Exception:
        # the traceback is the only thing that makes a crash diagnosable
        logging.exception('[main]\tUnhandled exception')
    finally:
        # `/restart` raises SystemExit from inside a handler task, and the
        # in-loop finally above does not reliably run in that case. stopping()
        # is idempotent, so calling it twice costs nothing.
        stopping()
