import os
import uuid
import subprocess
from session import popen_reader


def gen_uuid(length: int = 4) -> str:
    return str(uuid.uuid4())[:length]


def ocr_handler(img_bytes: bytes, lang: str = 'ch'):
    result = ''
    status = 200

    generated = gen_uuid()
    filename = f'/dev/shm/{generated}.png'
    output = f'/dev/shm/{generated}.txt'

    with open(filename, 'wb') as f:
        f.write(img_bytes)

    try:
        command = f'python3 ocr.py -i {filename} -l {lang} -o {output}'
        p = subprocess.Popen(command.split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        result, error = popen_reader(p)
        with open(output, 'r') as f:
            result = f.read()
    except FileNotFoundError:
        result = '未能识别出任何文字。'
        status = 500
    except Exception as e:
        result = str(e)
        status = 500
    finally:
        if os.path.exists(filename):
            os.remove(filename)
        if os.path.exists(output):
            os.remove(output)
        return result, status


def cap_handler(img_bytes: bytes, model: str = 'blip'):
    result = ''
    status = 200

    generated = gen_uuid()
    filename = f'/dev/shm/{generated}.png'
    output = f'/dev/shm/{generated}.txt'

    with open(filename, 'wb') as f:
        f.write(img_bytes)

    try:
        command = f'python3 cap.py -i {filename} -o {output} -m {model}'
        p = subprocess.Popen(command.split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        result, error = popen_reader(p)
        with open(output, 'r') as f:
            result = f.read()
    except FileNotFoundError:
        result = '图片识别失败。'
        status = 500
    except Exception as e:
        result = str(e)
        status = 500
    finally:
        if os.path.exists(filename):
            os.remove(filename)
        if os.path.exists(output):
            os.remove(output)
        return result, status
