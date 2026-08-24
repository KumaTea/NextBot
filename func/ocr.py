from share.auth import ensure_auth
from func.media_task import queue
from telethon.tl.custom import Message


CJK = {'ch', 'korean', 'japan', 'chinese_cht'}
LATIN = {'en', 'fr', 'german'}
SUPPORT = CJK | LATIN


@ensure_auth
async def command_ocr(event) -> Message:
    reply = await event.get_reply_message()
    if not (reply and reply.photo):
        return await event.respond('请回复一张图片。')

    text = event.raw_text
    lang = 'ch'
    inform_text = '正在识别中，请稍候。本功能运行在性能孱弱的路由器上，请耐心等待。'
    if len(text.split()) > 1:
        arg = text.split()[1].lower()
        if arg in SUPPORT:
            lang = arg
            inform_text += f'\n使用语言参数 `{lang}`。'
        else:
            inform_text += f'\n未知的语言参数(`{SUPPORT=}`)，使用默认值 `ch`。'

    inform = await event.respond(inform_text)
    if not await queue('ocr', event.chat_id, reply.id, inform.id, lang):
        return await inform.edit('识别服务没有响应，请稍后再试。')
    return inform
