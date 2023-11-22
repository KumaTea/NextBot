import asyncio
from mbot.session import bot
from mbot.handler import handler


async def main():
    async with bot:
        await handler()


if __name__ == '__main__':
    asyncio.run(main())
