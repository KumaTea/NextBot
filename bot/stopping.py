import logging
from bot.session import msg_store


def stopping():
    msg_store.save()
    logging.info('Stopping bot')
