import logging
from x.sync import on_callback as x_callback
from func.chat.cmd import gpt_callback_handler


async def process_callback(event):
    # Telethon hands callback data over as bytes, and there is no promise the
    # bytes are ours -- an old button from a previous build still arrives here.
    try:
        task = event.data.decode().split('_')[0]
    except (AttributeError, UnicodeDecodeError):
        logging.warning(f'[callbacks]\tUndecodable callback data: {event.data!r}')
        return await event.answer('未知任务', alert=True)

    if task == 'gpt':
        return await gpt_callback_handler(event)
    if task == 'x':
        return await x_callback(event)
    return await event.answer('未知任务', alert=True)
