import logging
import configparser
from bot.store import MsgStore
from telethon import TelegramClient
from openai import AsyncClient as aiClient


logging.basicConfig(
    format='%(asctime)s %(levelname)-8s %(message)s',
    level=logging.INFO,
    datefmt='%Y-%m-%d %H:%M:%S')

config = configparser.ConfigParser()
config.read('config.ini')

BOT_TOKEN = config['tg']['bot_token']

# `rbsk-tl.session`, deliberately not the old pyrogram `rbsk.session`:
# the two formats are incompatible, and keeping both files apart means
# the pyrogram session survives if you ever want to go back.
bot = TelegramClient(
    'rbsk-tl',
    int(config['tg']['api_id']),
    config['tg']['api_hash'],
)

gpt = aiClient(
    api_key=config['openai']['api_key'],
    base_url=config['openai']['endpoint'],
)

msg_store = MsgStore(client=bot)
