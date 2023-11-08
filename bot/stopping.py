import logging
from cmn.session import msg_store


def stopping():
    msg_store.save()
    logging.info('Stopping bot')
