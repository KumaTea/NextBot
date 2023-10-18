import re
from glossary import *
from session import logger
from pyrogram.types import Message
from bot_info import self_id, max_dialog
from bot_db import gpt_inst, cmd_re, multiuser_inst


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
    if custom_inst:
        thread = [{'role': 'system', 'content': custom_inst}]
    elif multiuser:
        thread = [{'role': 'system', 'content': multiuser_inst}]
    else:
        thread = [{'role': 'system', 'content': gpt_inst}]
    dialog_thread = []

    for message in dialogue:
        if message.text:
            text = trim_command(message.text) or ' '
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
    return thread
