import os


if os.name == 'nt':
    pwd = 'D:\\GitHub\\NextBot'
    TEMP_DIR = './data/dev/shm'
else:
    pwd = '/home/kuma/bots/rbsk'
    TEMP_DIR = '/dev/shm'

# REBOOT_CMD = "killall python3; killall tail"
REBOOT_CMD = (
    "kill $(ps aux | grep python3 | head -n 1 | awk '{print $2}'); "
    "kill $(ps aux | grep tail | head -n 1 | awk '{print $2}')"
)

url_regex = r'https?:\/\/(?:www\.|(?!www))[a-zA-Z0-9][a-zA-Z0-9-]+[a-zA-Z0-9]\.[^\s]{2,}|' \
            r'www\.[a-zA-Z0-9][a-zA-Z0-9-]+[a-zA-Z0-9]\.[^\s]{2,}|' \
            r'https?:\/\/(?:www\.|(?!www))[a-zA-Z0-9]+\.[^\s]{2,}|' \
            r'www\.[a-zA-Z0-9]+\.[^\s]{2,}'

cmd_re = r'^/\w+(@\w+)?[\s\n]'
start_user_re = r'^@[\w_]+:?\s?'

dm_start = (
    'Thank you for using Kuma Next bot!\n'
    'You may see commands sending "/help".'
)
dm_help = (
    '/start: wake me up\n'
    '/help: display this message\n'
    '/ping: check for delay\n'
    '/say: say something\n'
)
unknown_message = "I can't understand your message or command. You may try /help."

gpt_data_dir = os.path.join(pwd, 'data/gpt')
gpt_users_file = os.path.join(gpt_data_dir, 'users.txt')
msg_data_dir = os.path.join(pwd, 'data/msg')

group_help = (
    '/rp: repeat\n'
    '/title: manage titles\n'
    '`/help poll`: show poll help\n'
    '/ping: check for delay\n'
    '/debug: display debug info\n'
)

gpt_auth_info = (
    '本 bot 由不愿透露姓名的网友赞助，'
    '你目前还不在名单中，'
    '请等待一位管理员批准申请……'
)

bot_debug_info = (
    '本 bot 现正升级调试中，请稍后再调用。'
    '升级内容详见 [GitHub](https://github.com/KumaTea/NextBot)'
)

bot_commands = {
    'chat': ['chat', 'say', 'c'],
    'smart': ['smart', 's'],
    'debate': ['debate', 'd', 'g'],
    'ocr': ['ocr'],
    'cap': ['cap'],
}

MEDIA_BOT_CMD = '/opt/conda/envs/rbsk/bin/python3 mediabot.py >> /tmp/media.log 2>&1'

USER_AGENT = (
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
    'AppleWebKit/537.36 (KHTML, like Gecko) '
    'Chrome/122.0.0.0 '
    'Safari/537.36'
)
