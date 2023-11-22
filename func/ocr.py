import os
import asyncio
from pyrogram import Client
from bot.auth import ensure_not_bl
from pyrogram.types import Message
import requests
from bot.tools import gen_uuid
from pyrogram.enums.parse_mode import ParseMode


API = 'http://172.21.45.250:14500/ocr'
CJK = ['ch', 'korean', 'japan', 'chinese_cht']
LATIN = ['en', 'fr', 'german']
SUPPORT = CJK + LATIN


@ensure_not_bl
async def command_ocr(client: Client, message: Message) -> Message:
    reply = message.reply_to_message
    msg = None
    if reply.photo:
        msg = reply
    elif message.photo:
        msg = message
    if not msg:
        return await message.reply_text('请回复一张图片。', quote=False)

    text = message.text
    lang = 'ch'
    inform_text = '正在识别中，请稍候。本功能运行在性能孱弱的路由器上，请耐心等待。'
    if len(text.split()) > 1:
        arg = text.split()[1]
        if arg.lower() in SUPPORT:
            lang = arg.lower()
            inform_text += f'\n使用语言参数 `{lang}`。'
        else:
            inform_text += f'\n未知的语言参数(`{SUPPORT=}`)，使用默认值 `ch`。'

    filename = f'/dev/shm/ocr-{gen_uuid()}.png'
    dl, inform = await asyncio.gather(
        msg.download(filename),
        message.reply_text(inform_text, quote=False, parse_mode=ParseMode.MARKDOWN)
    )

    try:
        with open(filename, 'rb') as f:
            files = {'image': f}
            values = {'lang': lang}
            r = requests.post(API, files=files, data=values)
            result = r.json()['result']
            text = f'```\n{result}\n```'
            to_return = await inform.edit_text(text, parse_mode=ParseMode.MARKDOWN)
    except Exception as e:
        to_return = await inform.edit_text(f'Error: {e}')
    finally:
        os.remove(filename)

    return to_return
