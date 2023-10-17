from functions import *
from session import bot
from pyrogram import filters
from messages import process_msg
from callbacks import process_callback
from pyrogram.handlers import MessageHandler, CallbackQueryHandler


def register_handlers():
    # group commands
    bot.add_handler(MessageHandler(command_chat, filters.command(['chat', 'say']) & filters.group))

    # group messages
    bot.add_handler(MessageHandler(process_msg, filters.group))

    # callbacks
    bot.add_handler(CallbackQueryHandler(process_callback))
