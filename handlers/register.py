import logging
from telethon import events
from bot.session import bot
from common.info import username
from share.common import command_re
from handlers.functions import *  # noqa
from common.data import bot_commands
from handlers.messages import process_msg
from handlers.callbacks import process_callback


# Pyrogram stopped after the first matching handler in a group;
# Telethon runs every handler that matches. Remembering which commands
# we answer lets the catch-all message handler step out of the way.
registered_commands: set[str] = set()
_command_matcher = None

in_group = (lambda e: e.is_group)
in_private = (lambda e: e.is_private)


def on_command(callback, commands: list[str], where=None):
    registered_commands.update(commands)
    bot.add_event_handler(callback, events.NewMessage(
        incoming=True,
        pattern=command_re(commands, username),
        func=where
    ))


def is_a_command(event) -> bool:
    return bool(_command_matcher and _command_matcher.match(event.message.message or ''))


def register_handlers():
    global _command_matcher

    # group commands
    on_command(command_chat, bot_commands['chat'], in_group)
    on_command(command_smart, bot_commands['smart'], in_group)
    on_command(command_chat, bot_commands['debate'], in_group)
    # on_command(command_ocr, bot_commands['ocr'], in_group)
    # on_command(command_cap, bot_commands['cap'], in_group)
    on_command(command_allow_gpt, ['allow_gpt'], in_group)
    on_command(command_wiki, ['wiki'], in_group)
    # works in private chats as well, so no location filter
    on_command(command_transcribe, bot_commands['transcribe'])

    # private commands
    on_command(command_reboot, ['restart', 'reboot'], in_private)

    # everything is registered, so the catch-all knows what to skip
    _command_matcher = command_re(sorted(registered_commands), username)

    # group messages
    bot.add_event_handler(process_msg, events.NewMessage(
        incoming=True,
        func=lambda e: e.is_group and not is_a_command(e)
    ))

    # callbacks
    bot.add_event_handler(process_callback, events.CallbackQuery())

    return logging.info('Registered handlers')
