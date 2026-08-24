from bot.session import logging, msg_store


_stopped = False


def stopping():
    """
    Shut down cleanly. Safe to call more than once: `/restart` calls it from
    inside a handler, and `main` calls it again on the way out.
    """
    global _stopped
    if _stopped:
        return
    _stopped = True

    try:
        from x.sync import stop as stop_mirror
        stop_mirror()
    except Exception:
        logging.exception('Could not stop the X mirror cleanly')

    msg_store.stop_autosave()
    msg_store.save()
    logging.info('Stopping bot')
