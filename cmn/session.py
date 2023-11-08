import logging
import configparser
from gpt.gpt_auth import gpt_auth  # noqa
from bot.bot_store import MsgStore
from pyrogram import Client as tgClient
from openai import AsyncClient as aiClient


logging.basicConfig(
    format='%(asctime)s %(levelname)-8s %(message)s',
    level=logging.INFO,
    datefmt='%Y-%m-%d %H:%M:%S')
logger = logging.getLogger(__name__)

config = configparser.ConfigParser()
config.read('config.ini')

bot = tgClient(
    'rbsk',
    api_id=config['tg']['api_id'],
    api_hash=config['tg']['api_hash'],
    bot_token=config['tg']['bot_token'],
)

gpt = aiClient(
    api_key=config['openai']['api_key'],
    organization=config['openai']['organization']
)

gpt_model = config['openai']['model']
msg_store = MsgStore()
