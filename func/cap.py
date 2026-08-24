from share.auth import ensure_auth
from func.media_task import queue
from telethon.tl.custom import Message


MODELS = {'blip', 'git'}


@ensure_auth
async def command_cap(event) -> Message:
    reply = await event.get_reply_message()
    if not (reply and reply.photo):
        return await event.respond('请回复一张图片。')

    text = event.raw_text
    model = 'blip'
    inform_text = '正在识别中，请稍候。本功能运行在性能孱弱的路由器上，请耐心等待。'
    if len(text.split()) > 1:
        arg = text.split()[1].lower()
        if arg in MODELS:
            model = arg
            inform_text += f'\n使用模型 `{model}`。'
        else:
            inform_text += f'\n未知的语言参数(`{MODELS=}`)，使用默认值 `{model}`。'

    inform = await event.respond(inform_text)
    if not await queue('cap', event.chat_id, reply.id, inform.id, model):
        return await inform.edit('识别服务没有响应，请稍后再试。')
    return inform
