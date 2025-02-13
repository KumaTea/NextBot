# An async http server
# handling whisper requests
# of both url and file
# exit after given idle time


from v2t.base import logging
# from v2t.whisper import *
from v2t.idle import create_idle_task


create_idle_task()


from v2t.web import app

logging.info('Starting server...')
