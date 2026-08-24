import re
from bot.session import logging
from telethon.tl.custom import Message
from gpt.glossary import words, nicknames
from telethon.extensions import markdown
from common import info
from common.info import max_dialog
from common.data import cmd_re, bot_commands, start_user_re
from gpt.data import gpt_inst, smart_inst, debate_inst, multiuser_inst, assistant_username


cmd_pattern = re.compile(cmd_re)
username_re = re.compile(start_user_re)


def trim_command(text: str) -> str:
    """
    before: /command@botname text
    before: /command text
    after: text
    """
    if ' ' in text:
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
    username = username_re.match(text)
    if username:
        logging.info(f'[func_chat]\tbefore: {text} after: {text[username.end():]}')
        text = text[username.end():]
    return text


def unparse_markdown(message: Message) -> str:
    """Plain text with its entities written back as markdown."""
    return markdown.unparse(message.message, message.entities)


def process_message(message: Message) -> str:
    text = unparse_markdown(message) if message.entities else message.raw_text
    return trim_command(text or '')


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


def get_cmd_type(text: str) -> str:
    for cmd_type in bot_commands:  # 'chat', 'smart', 'debate'
        for cmd in bot_commands[cmd_type]:  # 'chat', 'c', etc.
            if text.startswith(f'/{cmd}'):
                return cmd_type
    return 'chat'


def speaker_name(message: Message) -> str:
    """How to address whoever wrote a message in the GPT thread."""
    sender = message.sender
    if sender:
        return sender.username or sender.first_name or str(message.sender_id)
    return str(message.sender_id)


def gen_thread(dialogue: list[Message], custom_inst: str = None) -> list[dict]:
    # only keep messages sent by an actual user
    dialogue = [m for m in dialogue if m and m.sender_id and m.sender_id > 0]
    if not dialogue:
        return []
    # only the last few turns are sent, so do not spend work rendering the rest
    dialogue = dialogue[-max_dialog:]

    # detect multiuser
    user_ids = set(m.sender_id for m in dialogue) | {info.self_id}
    multiuser = len(user_ids) > 2

    # generate instructions
    inst = {}
    if custom_inst:
        inst = {'role': 'system', 'content': custom_inst}
    else:
        first_msg_text = dialogue[0].raw_text
        if first_msg_text:
            command = get_cmd_type(first_msg_text)
            if command == 'smart':
                inst = {'role': 'system', 'content': f'{smart_inst}'}
            elif command == 'debate':
                inst = {'role': 'system', 'content': debate_inst}
    if not inst:
        inst = {'role': 'system', 'content': f'{gpt_inst}'}
    if multiuser:
        inst['content'] += ' ' + multiuser_inst

    # initialize thread
    thread = [inst]
    dialog_thread = []

    # generate dialog thread
    for message in dialogue:
        if not message.raw_text:
            continue
        text = process_message(message) or ' '
        if message.sender_id == info.self_id:
            role = 'assistant'
            username_string = f'{assistant_username}: '
        else:
            role = 'user'
            username_string = f'@{speaker_name(message)}: '
        content = username_string + bot_to_gpt(text) if multiuser else bot_to_gpt(text)
        dialog_thread.append({'role': role, 'content': content})
    thread.extend(dialog_thread)

    # logged once -- this used to print every message and then the whole
    # thread again as a pretty-printed block
    for m in thread:
        logging.info(f"[func_chat]\t{m['role']}: {m['content'][:200]}")
    return thread
