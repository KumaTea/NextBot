from mbot.session import bot
from mbot.handler import handler, StatHolder, STATUS_FILE


holder = StatHolder(STATUS_FILE)


async def main():
    async with bot:
        await handler(bot)


if __name__ == '__main__':
    with holder:
        bot.run(main())
