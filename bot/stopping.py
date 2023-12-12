from bot.session import msg_store, logging


def stopping():
    msg_store.save()
    logging.info('Stopping bot')
