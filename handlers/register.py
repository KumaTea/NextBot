from bot.session import bot
from pyrogram import filters
from handlers.functions import *
from common.data import bot_commands
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
    bot.add_handler(MessageHandler(command_allow_gpt, filters.command(['allow_gpt']) & filters.group))

    # group messages
    bot.add_handler(MessageHandler(process_msg, filters.group))

    # private commands
    bot.add_handler(MessageHandler(command_reboot, filters.command(['restart', 'reboot']) & filters.private))

    # callbacks
    bot.add_handler(CallbackQueryHandler(process_callback))
