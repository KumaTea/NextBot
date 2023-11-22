import configparser
from pyrogram import Client as tgClient


config = configparser.ConfigParser()
config.read('config.ini')

bot = tgClient(
    'media',
    api_id=config['tg']['api_id'],
    api_hash=config['tg']['api_hash'],
    bot_token=config['tg']['bot_token'],
)
