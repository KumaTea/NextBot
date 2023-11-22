import asyncio
from mbot.session import bot
from mbot.handler import handler


if __name__ == '__main__':
    try:
        bot.start()
        asyncio.run(handler())
    except:
        bot.stop()
