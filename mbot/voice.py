import logging
from cmn.data import *
from bot.tools import gen_uuid
from bot.session import sync_gpt
from pyrogram.types import Message
from pyrogram.enums.parse_mode import ParseMode
from mbot.common import set_work, set_free


def save_voice(message: Message) -> str:
    """
    Save the voice message to a file.
    :param message: The message object.
    :return: The path of the saved file.
    """
    file_name = gen_uuid()
    file_path = f'/dev/shm/{file_name}.ogg'
    message.download(file_path)
    return file_path


def transcribe_voice(voice_path: str) -> str:
    with open(voice_path, 'rb') as voice:
        transcript = sync_gpt.audio.transcriptions.create(
            model='whisper-1',
            file=voice,
            language='zh'
        )
    text = transcript.text
    logging.info(f'[func_voice]\t{text}')

    if not text.strip():
        return '啥也没说'
    for word in whisper_blacklist:
        if word in text:
            return '啥也没说'

    return text


def process_voice(chat_id: int, voice_id: int, inform_id: int):
    set_work()

    from bot.session import bot
    with bot:

        message = bot.get_messages(chat_id, voice_id)
        inform = bot.get_messages(chat_id, inform_id)
        voice_path = None

        try:
            voice_path = save_voice(message)

            if message.from_user:
                user_mention = message.from_user.mention(style=ParseMode.MARKDOWN)
                if message.forward_from:
                    user_mention += ' 🔊 ' + message.forward_from.mention(style=ParseMode.MARKDOWN)
            elif message.sender_chat:
                if message.sender_chat.username:
                    user_mention = f'[{message.sender_chat.title}](tg://resolve?domain={message.sender_chat.username})'
                else:
                    user_mention = message.sender_chat.title
            else:
                user_mention = '😎'

            transcription = transcribe_voice(voice_path)
            text = user_mention + ':\n' + transcription + '\n' + voice_tag
            # setattr(message, 'transcription', transcription)
            # msg_store.add(message)
            inform = inform.edit_text(text, parse_mode=ParseMode.MARKDOWN)
        except Exception as e:
            logging.warning(f'[func_voice]\tERROR!!!')
            logging.warning(f'[func_voice]\t{e}')
            inform = inform.edit_text('听不懂捏')
        finally:
            if voice_path and os.path.isfile(voice_path):
                os.remove(voice_path)

    del bot

    set_free()
    return inform
