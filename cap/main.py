from session import logging
from handler import cap_handler  # , ocr_handler
from flask import Flask, request, jsonify


app = Flask(__name__)


@app.route('/ocr', methods=['POST'])
def ocr():
    if request.method == 'POST':
        logging.info('[OCR]\treceived request...')
        if request.files:
            # image = request.files['image'].read()
            # lang = request.form.get('lang', 'ch')
            # logging.info(f'[OCR]\tprocessing...')
            # result, status = ocr_handler(image, lang)
            # logging.info('[OCR]\tresponding...')
            # return jsonify({'result': result}), status
            return jsonify({'result': '由于本机 CPU 不支持 AVX 指令集，OCR 功能暂时停用'}), 200
        else:
            return jsonify({'error': 'No image received.'}), 404


@app.route('/cap', methods=['POST'])
def cap():
    if request.method == 'POST':
        logging.info('[CAP]\treceived request...')
        if request.files:
            image = request.files['image'].read()
            model = request.form.get('model', 'blip')
            logging.info(f'[CAP]\tprocessing...')
            result, status = cap_handler(image, model)
            logging.info('[CAP]\tresponding...')
            return jsonify({'result': result}), status
        else:
            return jsonify({'error': 'No image received.'}), 404


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=14500, debug=False)
