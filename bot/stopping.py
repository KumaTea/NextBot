from bot.session import msg_store, logger


def stopping():
    msg_store.save()
    logger.info('Stopping bot')
