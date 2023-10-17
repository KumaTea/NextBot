import re
from bot_info import self_id
from bot_db import gpt_inst, cmd_re
from pyrogram.types import Message


def trim_command(text: str) -> str:
    """
    before: /command@botname text
    before: /command text
    after: text
    """
    if ' ' in text:
        cmd_pattern = re.compile(cmd_re)
        cmd = cmd_pattern.match(text)
        if cmd:
            return text[cmd.end():]
        else:
            return text
    else:
        if text.startswith('/'):
            return ''
        else:
            return text


def gen_thread(dialogue: list[Message]) -> list[dict]:
    thread = [{'role': 'system', 'content': gpt_inst}]
    multiuser = False

    user_ids = list(set([m.from_user.id for m in dialogue]))
    if len(user_ids) > 2:
        multiuser = True

    for message in dialogue:
        if message.text:
            text = trim_command(message.text) or ' '
            if multiuser:
                if message.from_user.id == self_id:
                    thread.append({'role': 'assistant', 'content': '@ChatGPT: ' + text})
                else:
                    thread.append({'role': 'user', 'content': f'@{message.from_user.username}: {text}'})
            else:
                if message.from_user.id == self_id:
                    thread.append({'role': 'assistant', 'content': text})
                else:
                    thread.append({'role': 'user', 'content': text})
    return thread
