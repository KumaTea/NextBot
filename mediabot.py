import logging
from flask import Flask, request
from mbot.handler import ocr_handler, voice_handler


logging.basicConfig(
    format='%(asctime)s %(levelname)-8s %(message)s',
    level=logging.INFO,
    datefmt='%Y-%m-%d %H:%M:%S')
logger = logging.getLogger(__name__)


app = Flask(__name__)


@app.route('/ocr', methods=['GET'])
def ocr():
    logger.info('[media]\treceived request...')
    chat_id = int(request.args.get('chat_id'))
    reply_id = int(request.args.get('reply_id'))
    inform_id = int(request.args.get('inform_id'))
    lang = request.args.get('lang')
    return ocr_handler(chat_id, reply_id, inform_id, lang)


@app.route('/voice', methods=['GET'])
def voice():
    logger.info('[media]\treceived request...')
    chat_id = int(request.args.get('chat_id'))
    voice_id = int(request.args.get('voice_id'))
    inform_id = int(request.args.get('inform_id'))
    return voice_handler(chat_id, voice_id, inform_id)


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=13600, debug=False)
