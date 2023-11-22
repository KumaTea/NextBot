from threading import Thread
from mbot.ocr import process_ocr
from mbot.voice import process_voice


def ocr_handler(chat_id: int, reply_id: int, inform_id: int, lang: str = 'ch'):
    t = Thread(target=process_ocr, args=(chat_id, reply_id, inform_id, lang))
    t.start()
    return 'OK'


def voice_handler(chat_id: int, voice_id: int, inform_id: int):
    t = Thread(target=process_voice, args=(chat_id, voice_id, inform_id))
    t.start()
    return 'OK'
