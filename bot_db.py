import os


if os.name == 'nt':
    pwd = 'D:\\GitHub\\NextBot'
else:
    pwd = '/home/kuma/bots/rbsk'

url_regex = r'https?:\/\/(?:www\.|(?!www))[a-zA-Z0-9][a-zA-Z0-9-]+[a-zA-Z0-9]\.[^\s]{2,}|' \
            r'www\.[a-zA-Z0-9][a-zA-Z0-9-]+[a-zA-Z0-9]\.[^\s]{2,}|' \
            r'https?:\/\/(?:www\.|(?!www))[a-zA-Z0-9]+\.[^\s]{2,}|' \
            r'www\.[a-zA-Z0-9]+\.[^\s]{2,}'

cmd_re = r'^/\w+(@\w+)?\s'

gpt_inst = ("You are ChatGPT. "
            "You're in a group chat. "
            "You must reply in their language. "
            "Reply should be short, casual and relaxed. "
            "Be like a friend, not an assistant.")

multiuser_inst = (f'{gpt_inst} '
                  f'Format is "@username: message", '
                  f'your reply must start with "@ChatGPT: ".')

# credit: https://arxiv.org/abs/2309.03409
magic_prompt = 'Take a deep breath and work on this problem step-by-step. '
less_magic_prompt = 'Break the question down.'

smart_inst = (
    'You are ChatGPT, '
    'a knowledgeable and intelligent scholar. '
    'You possess the wisdom and experience of a seasoned expert. '
    'You are friendly, neutral and informative, '
    'eager to assist and inform others to the best of your ability. '
    'You are open-minded and curious, never hesitating to dive into new topics. '
    'You are very creative, always try your best to provide an answer, even to the most difficult questions. '
    'You are here to help, so there is no need for a "can\'t" in your vocabulary.'
    '\n'
    'You must reply in the language of the question asked. '
    f'You should {less_magic_prompt}, and start your answer with "{magic_prompt}" in that language.'
)


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

group_help = (
    '/rp: repeat\n'
    '/title: manage titles\n'
    '`/help poll`: show poll help\n'
    '/ping: check for delay\n'
    '/debug: display debug info\n'
)

gpt_auth_info = (
    '本 bot 由不愿透露姓名的莱姆老师赞助，'
    '你目前还不在名单中，'
    '请等待一位管理员批准申请……'
)
