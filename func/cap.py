import os
import asyncio
from pyrogram import Client
from bot.auth import ensure_not_bl
from pyrogram.types import Message
from common.data import TEMP_DIR, MEDIA_BOT_CMD
from pyrogram.enums.parse_mode import ParseMode


MODELS = ['blip', 'git']
TASK_FILE = f'{TEMP_DIR}/task.txt'
STATUS_FILE = f'{TEMP_DIR}/media.run'


@ensure_not_bl
async def command_cap(client: Client, message: Message) -> Message:
    reply = message.reply_to_message
    if not (reply and reply.photo):
        return await message.reply_text('请回复一张图片。', quote=False)

    text = message.text
    model = 'blip'
    inform_text = '正在识别中，请稍候。本功能运行在性能孱弱的路由器上，请耐心等待。'
    if len(text.split()) > 1:
        arg = text.split()[1]
        if arg.lower() in MODELS:
            model = arg.lower()
            inform_text += f'\n使用模型 `{model}`。'
        else:
            inform_text += f'\n未知的语言参数(`{MODELS=}`)，使用默认值 `{model}`。'

    inform = await message.reply_text(inform_text, quote=False, parse_mode=ParseMode.MARKDOWN)
    chat_id = message.chat.id
    reply_id = reply.id
    inform_id = inform.id
    with open(TASK_FILE, 'a') as f:
        # append task to file
        f.write(','.join(list(map(str, ['cap', chat_id, reply_id, inform_id, model]))) + '\n')

    while os.path.isfile(STATUS_FILE):
        await asyncio.sleep(1)
    await asyncio.create_subprocess_shell(MEDIA_BOT_CMD)
    return inform
