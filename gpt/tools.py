import re
import pprint
from bot.session import logging
from pyrogram.types import Message
from gpt.glossary import words, nicknames
from pyrogram.parser.parser import Parser
from common.info import self_id, max_dialog
from common.data import cmd_re, start_user_re, bot_commands
from gpt.data import gpt_inst, multiuser_inst, search_inst, web_inst, smart_inst, debate_inst


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


def get_cmd_type(text: str) -> str:
    for cmd_type in bot_commands:  # 'chat', 'smart', 'debate'
        for cmd in bot_commands[cmd_type]:  # 'chat', 'c', etc.
            if text.startswith(f'/{cmd}'):
                return cmd_type
    return 'chat'


def gen_thread(dialogue: list[Message], custom_inst: str = None, search_result: str = None) -> list[dict]:
    # detect multiuser
    multiuser = False
    for m in dialogue.copy():
        if not m.from_user:
            dialogue.remove(m)
    user_ids = list(set([m.from_user.id for m in dialogue] + [self_id]))
    if len(user_ids) > 2:
        multiuser = True

    # generate instructions
    inst = {}
    if custom_inst:
        inst = {'role': 'system', 'content': custom_inst}
    elif search_result:
        inst = {'role': 'system', 'content': f'{gpt_inst} {web_inst}'}
    else:
        first_msg_text = dialogue[0].text
        if first_msg_text:
            command = get_cmd_type(first_msg_text)
            if command == 'smart':
                inst = {'role': 'system', 'content': f'{smart_inst} {search_inst}'}
            elif command == 'debate':
                inst = {'role': 'system', 'content': debate_inst}
    if not inst:
        inst = {'role': 'system', 'content': f'{gpt_inst} {search_inst}'}
    if multiuser:
        inst['content'] += ' ' + multiuser_inst

    # initialize thread
    thread = [inst]
    dialog_thread = []

    # generate dialog thread
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
        logging.info(f'[func_chat]\t' + m['role'] + ': ' + m['content'])
    dialog_thread = dialog_thread[-max_dialog:]
    thread.extend(dialog_thread)

    # add search result
    if search_result:
        search_result_text = 'Web Search Result:\n' + search_result
        thread.append({'role': 'system', 'content': search_result_text})

    logging.info(pprint.pformat(thread, indent=2))
    return thread
