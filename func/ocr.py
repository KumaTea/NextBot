import requests
from pyrogram import Client
from bot.auth import ensure_not_bl
from pyrogram.types import Message
from pyrogram.enums.parse_mode import ParseMode


LOCAL_API = 'http://127.0.0.1:13600/ocr'
CJK = ['ch', 'korean', 'japan', 'chinese_cht']
LATIN = ['en', 'fr', 'german']
SUPPORT = CJK + LATIN


@ensure_not_bl
async def command_ocr(client: Client, message: Message):
    reply = message.reply_to_message
    if not (reply and reply.photo):
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

    inform = await message.reply_text(inform_text, quote=False, parse_mode=ParseMode.MARKDOWN)
    r = requests.get(
        LOCAL_API,
        params={
            'chat_id': message.chat.id,
            'reply_id': reply.id,
            'inform_id': inform.id,
            'lang': lang
        }
    )
    return r
