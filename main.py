import os

if os.name == 'posix':
    import uvloop
    uvloop.install()

from bot.starting import starting
from bot.stopping import stopping
from bot.session import bot, logging


starting()


if __name__ == '__main__':
    try:
        bot.run()
    except Exception as e:
        logging.warning('[main]\tException')
        logging.warning(f'{e=}')
    finally:
        stopping()
