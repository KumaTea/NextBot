from common.data import *
from bot.session import bot
from pyrogram import filters
from handlers.functions import *
from handlers.messages import process_msg
from handlers.callbacks import process_callback
from pyrogram.handlers import MessageHandler, CallbackQueryHandler


def register_handlers():
    # group commands
    bot.add_handler(MessageHandler(command_chat, filters.command(bot_commands['chat']) & filters.group))
    bot.add_handler(MessageHandler(command_smart, filters.command(bot_commands['smart']) & filters.group))
    bot.add_handler(MessageHandler(command_chat, filters.command(bot_commands['debate']) & filters.group))
    bot.add_handler(MessageHandler(command_ocr, filters.command(bot_commands['ocr']) & filters.group))
    bot.add_handler(MessageHandler(command_cap, filters.command(bot_commands['cap']) & filters.group))

    # group messages
    bot.add_handler(MessageHandler(process_msg, filters.group))

    # callbacks
    bot.add_handler(CallbackQueryHandler(process_callback))
