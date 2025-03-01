import sys
from pyrogram import Client
from bot.stopping import stopping
from pyrogram.types import Message
# from common.data import REBOOT_CMD
from common.info import administrators


# @ensure_auth
# already checked
async def command_reboot(client: Client, message: Message):
    if message.from_user.id in administrators:
        await message.reply('Restarting...')
        # return os.system(REBOOT_CMD)
        stopping()
        return sys.exit(0)
    # sys.exit() additionally raises a SystemExit exception,
    # offering flexibility by allowing the passing of an optional exit status or error message as an argument.
    # os._exit() brings about an immediate termination of the process without executing any cleanup operations.
    # https://www.analyticsvidhya.com/blog/2024/01/python-exit-commands-quit-exit-sys-exit-and-os-_exit/
    else:
        return None
