import os
import time
from pathlib import Path
from cmn.data import TEMP_DIR


work_status_file = os.path.join(TEMP_DIR, 'media.work')


def set_work():
    while os.path.isfile(work_status_file):
        time.sleep(1)
    Path(work_status_file).touch()


def set_free():
    if os.path.isfile(work_status_file):
        os.remove(work_status_file)
