import os

if os.name == 'posix':
    import uvloop
    uvloop.install()

from bot.starting import starting
from bot.stopping import stopping
from cmn.session import bot, logger


starting()


if __name__ == '__main__':
    try:
        bot.run()
    except Exception as e:
        logger.warning('[main]\tException')
        logger.warning(f'{e=}')
    finally:
        stopping()
