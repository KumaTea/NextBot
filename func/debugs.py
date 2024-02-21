import os
from pyrogram import Client
from pyrogram.types import Message
from common.info import administrators
from common.data import REBOOT_CMD


# @ensure_auth
# already checked
async def command_reboot(client: Client, message: Message):
    if message.from_user.id in administrators:
        await message.reply('Restarting...')
        return os.system(REBOOT_CMD)
    else:
        return None
