from bot.session import logging, msg_store


def stopping():
    msg_store.save()
    logging.info('Stopping bot')
