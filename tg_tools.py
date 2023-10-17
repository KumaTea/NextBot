from pyrogram import Client
from pyrogram.types import Message


async def get_dialog(client: Client, message: Message) -> list[Message]:
    dialog = [message]
    msg = message
    while msg.reply_to_message:
        replies = await client.get_messages(msg.chat.id, [msg.reply_to_message.id])
        reply = replies[0]
        dialog.insert(0, reply)
        msg = reply
    return dialog
