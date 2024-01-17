import logging
from common.tools import get_url_int_list  # , get_url_str_list


LOCAL_URL = 'https://hm.lan.kmtea.eu'


logging.warning('Loading local data...')

trusted_group = get_url_int_list(f'{LOCAL_URL}/trusted-group.txt')
logging.warning(f'Trusted groups: {len(trusted_group)}')
bl_users = get_url_int_list(f'{LOCAL_URL}/bl-users.txt')
logging.warning(f'Blacklisted users: {len(bl_users)}')
known_group = trusted_group.copy()
known_group.extend(get_url_int_list(f'{LOCAL_URL}/known-group.txt'))
logging.warning(f'Known groups: {len(known_group)}')

# blacklist_words = get_url_str_list(f'{LOCAL_URL}/blacklist-words.txt')

known_user_ids = get_url_int_list(f'{LOCAL_URL}/known-user-ids.txt')
logging.warning(f'Known users: {len(known_user_ids)}')
