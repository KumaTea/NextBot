import logging
from typing import List
from urllib.request import urlopen


LOCAL_URL = 'https://us.lan.kmtea.eu'


def get_url_text(url: str) -> str:
    with urlopen(url) as response:
        return response.read().decode('utf-8')


def process_text(text: str) -> str:
    text = text.replace(',', '')
    text = text.replace('\t', '')
    text = text.strip()
    text = text.split('#')[0]
    text = text.split(' ')[0]
    return text


def get_url_int(url: str) -> List[int]:
    int_list = []
    text = get_url_text(url)
    for line in text.splitlines():
        num_text = process_text(line)
        if num_text:
            num = int(num_text)
            int_list.append(num)

    return int_list


def get_url_str(url: str) -> List[str]:
    str_list = []
    text = get_url_text(url)
    for line in text.splitlines():
        str_text = process_text(line)
        if str_text:
            str_list.append(str_text)

    return str_list


logging.warning('Loading local data...')
trusted_group = get_url_int(f'{LOCAL_URL}/trusted-group.txt')
logging.warning(f'Trusted groups: {len(trusted_group)}')
bl_users = get_url_int(f'{LOCAL_URL}/bl-users.txt')
logging.warning(f'Blacklisted users: {len(bl_users)}')

known_group = trusted_group.copy()
known_group.extend(get_url_int(f'{LOCAL_URL}/known-group.txt'))
logging.warning(f'Known groups: {len(known_group)}')

# blacklist_words = get_url_str(f'{LOCAL_URL}/blacklist-words.txt')
