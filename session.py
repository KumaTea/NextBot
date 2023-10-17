import openai
import logging
import configparser
from bot_info import *
from pyrogram import Client


logging.basicConfig(
    format='%(asctime)s %(levelname)-8s %(message)s',
    level=logging.INFO,
    datefmt='%Y-%m-%d %H:%M:%S')
logger = logging.getLogger(__name__)

config = configparser.ConfigParser()
config.read('config.ini')

bot = Client(
    'rbsk',
    api_id=config['tg']['api_id'],
    api_hash=config['tg']['api_hash'],
    bot_token=config['tg']['bot_token'],
)

openai.organization = config['openai']['organization']
openai.api_key = config['openai']['api_key']
gpt_model = config['openai']['model']
