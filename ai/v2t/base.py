import logging

logging.basicConfig(
    format='%(asctime)s.%(msecs)03d %(levelname)-8s %(message)s',
    level=logging.INFO,
    datefmt='%m-%d %H:%M:%S')


logging.info('Loading basic libraries')


import sys
import time
import asyncio
from dataclasses import dataclass
from datetime import datetime, timedelta
