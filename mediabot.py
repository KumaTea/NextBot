from mbot.session import bot
from mbot.handler import handler, STATUS_FILE, StatHolder


holder = StatHolder(STATUS_FILE)


async def main():
    async with bot:
        await handler(bot)


if __name__ == '__main__':
    with holder:
        bot.run(main())
