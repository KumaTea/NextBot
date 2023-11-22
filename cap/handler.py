import os
import time
import subprocess


def ocr_handler(img_bytes: bytes, lang: str = 'ch'):
    result = ''
    status = 200

    filename = f'/dev/shm/{int(time.time())}.png'
    output = f'/dev/shm/{int(time.time())}.txt'
    while os.path.exists(filename) or os.path.exists(output):
        time.sleep(0.1)
        filename = f'/dev/shm/{int(time.time())}.png'
        output = f'/dev/shm/{int(time.time())}.txt'

    with open(filename, 'wb') as f:
        f.write(img_bytes)

    try:
        command = f'python3 ocr.py -i {filename} -l {lang} -o {output}'
        subprocess.run(command.split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        with open(output, 'r') as f:
            result = f.read()
    except Exception as e:
        result = str(e)
        status = 500
    finally:
        if os.path.exists(filename):
            os.remove(filename)
        if os.path.exists(output):
            os.remove(output)
        return result, status
