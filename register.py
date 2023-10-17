from functions import *
from session import bot
from pyrogram import filters
from pyrogram.handlers import MessageHandler


def register_handlers():
    bot.add_handler(MessageHandler(chat, filters.command(['chat', 'say']) & filters.group))
