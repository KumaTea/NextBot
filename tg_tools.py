from pyrogram import Client
from bot_info import max_dialog
from pyrogram.types import Message
from session import bot, msg_store, logger


async def get_message(chat_id: int, msg_id: int, client: Client = bot) -> Message:
    msg = msg_store.get(chat_id, msg_id)
    if not msg:
        msg = await client.get_messages(chat_id, msg_id)
        msg_store.add(msg)
        logger.info(f'[tg_tools]\t\tGet message {msg_id} via API')
    else:
        logger.info(f'[tg_tools]\t\tGet message {msg_id} via cache')
    return msg


async def get_dialog(client: Client, message: Message) -> list[Message]:
    dialog = [message]
    msg = message
    dialog_count = 0
    while msg.reply_to_message:
        reply = await get_message(msg.chat.id, msg.reply_to_message.id)
        dialog.insert(0, reply)
        msg = reply
        dialog_count += 1
        if dialog_count >= max_dialog:
            break
    return dialog
