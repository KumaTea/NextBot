from mbot.session import bot
from mbot.handler import handler


async def main():
    async with bot:
        await handler(bot)


if __name__ == '__main__':
    bot.run(main())
