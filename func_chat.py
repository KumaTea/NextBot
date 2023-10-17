import asyncio
from pyrogram import Client
from pyrogram.types import Message
from pyrogram.enums.parse_mode import ParseMode
from gpt_core import stream_chat_by_sentences
from typing import Union, AsyncGenerator
from gpt_tools import gen_thread
from tg_tools import get_dialog


async def type_in_message(message: Message, generator: AsyncGenerator[str, None]) -> Message:
    text = ''
    msg = message
    parse_mode = None
    async for chunk in generator:
        text += chunk
        if '`' in text:
            parse_mode = ParseMode.MARKDOWN
        if text.lower().startswith('@chatgpt: '):
            index = text.lower().find('@chatgpt: ')
            text = text[index+9:]
        msg = await msg.edit_text(text, parse_mode=parse_mode)
    return msg


async def chat(client: Client, message: Message) -> Union[Message, None]:
    command = message.text
    content_index = command.find(' ')
    reply = message.reply_to_message
    if content_index == -1:
        # no text
        if not reply:
            return None

    dialog, resp_message = await asyncio.gather(
        get_dialog(client, message),
        message.reply_text('...', quote=False)
    )

    thread = gen_thread(dialog)
    return await type_in_message(resp_message, stream_chat_by_sentences(thread))
