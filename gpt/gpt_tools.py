import re
from bot.bot_db import *
from gpt.glossary import *
from cmn.session import logger
from pprint import PrettyPrinter
from pyrogram.types import Message
from pyrogram.parser.parser import Parser
from bot.bot_info import self_id, max_dialog


def trim_command(text: str) -> str:
    """
    before: /command@botname text
    before: /command text
    after: text
    """
    if ' ' in text:
        cmd_pattern = re.compile(cmd_re)
        cmd = cmd_pattern.match(text)
        while cmd:
            text = text[cmd.end():]
            cmd = cmd_pattern.match(text)
        return text
    else:
        if text.startswith('/'):
            return ''
        else:
            return text


def trim_starting_username(text: str) -> str:
    """
    before: @botname text
    after: text
    """
    username_re = re.compile(r'^@[\w_]+:?\s?')
    username = username_re.match(text)
    if username:
        logger.info(f'[func_chat]\tbefore: {text} after: {text[username.end():]}')
        text = text[username.end():]
    return text


def unparse_markdown(message: Message) -> str:
    p = Parser(client=None)
    result = p.unparse(
        text=message.text,
        entities=message.entities,
        is_html=False
    )
    return result


def process_message(message: Message) -> str:
    if message.entities:
        text = unparse_markdown(message)
    else:
        text = message.text
    text = trim_command(text)
    # text = trim_starting_username(text)
    return text


def bot_to_gpt(text: str) -> str:
    # words
    for slang in words:
        text = text.replace(slang, words[slang])

    # nicknames
    for username in nicknames:
        for nickname in nicknames[username]:
            if nickname.lower() in text.lower():
                text = text.replace(nickname, f'@{username}')
                break

    return text


def gpt_to_bot(text: str) -> str:
    # words
    for slang in words:
        text = text.replace(words[slang], slang)

    # nicknames
    for username in nicknames:
        if f'@{username}' in text:
            text = text.replace(f'@{username}', nicknames[username][0])

    return text


def gen_thread(dialogue: list[Message], custom_inst: str = None) -> list[dict]:
    multiuser = False

    user_ids = list(set([m.from_user.id for m in dialogue] + [self_id]))
    if len(user_ids) > 2:
        multiuser = True

    inst = {}
    if custom_inst:
        inst = {'role': 'system', 'content': custom_inst}
    else:
        first_msg_text = dialogue[0].text
        if first_msg_text:
            command = ''
            for cmd_type in bot_commands:  # 'chat', 'smart', 'debate'
                for cmd in bot_commands[cmd_type]:  # 'chat', 'c', etc.
                    if first_msg_text.startswith(f'/{cmd}'):
                        command = cmd_type
                        break
            if command == 'smart':
                inst = {'role': 'system', 'content': smart_inst}
            elif command == 'debate':
                inst = {'role': 'system', 'content': debate_inst}
    if not inst:
        inst = {'role': 'system', 'content': gpt_inst}
    if multiuser:
        inst['content'] += ' ' + multiuser_inst

    thread = [inst]
    dialog_thread = []

    for message in dialogue:
        if message.text:
            text = process_message(message) or ' '
            if message.from_user.id == self_id:
                role = 'assistant'
                username_string = '@ChatGPT: '
            else:
                role = 'user'
                username_string = f'@{message.from_user.username or message.from_user.first_name}: '
            if multiuser:
                dialog_thread.append({'role': role, 'content': username_string + bot_to_gpt(text)})
            else:
                dialog_thread.append({'role': role, 'content': f'{bot_to_gpt(text)}'})
    for m in dialog_thread:
        logger.info(f'[func_chat]\t' + m['role'] + ': ' + m['content'])
    dialog_thread = dialog_thread[-max_dialog:]
    thread.extend(dialog_thread)
    PrettyPrinter().pprint(thread)
    return thread
