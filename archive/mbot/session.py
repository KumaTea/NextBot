import configparser
from pyrogram import Client


config = configparser.ConfigParser()
config.read('config.ini')

bot = Client(
    'media',
    api_id=config['tg']['api_id'],
    api_hash=config['tg']['api_hash'],
    bot_token=config['tg']['bot_token'],
)
