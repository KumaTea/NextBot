"""Tunables for the Telegram -> X mirror.

Identifiers live in `common.info` next to the other hard-coded ids; only the
operational switches are read from `config.ini`, so they can be flipped without
touching code.
"""

import os
import logging
from common.data import pwd
from bot.session import config


def _flag(name: str, default: bool) -> bool:
    try:
        return config['x'].getboolean(name, fallback=default)
    except KeyError:
        # no [x] section at all -- run with the defaults
        return default
    except ValueError:
        logging.warning(f'[x_config]	{name} is not a boolean, using {default}')
        return default


x_data_dir = os.path.join(pwd, 'data/x')
cookies_file = os.path.join(x_data_dir, 'cookies.json')
store_file = os.path.join(x_data_dir, 'synced.json')

# Master switch. Turning this off leaves every other bot function untouched.
enabled = _flag('enabled', True)
# Render and log what would be posted, but never talk to X.
dry_run = _flag('dry_run', False)
# Append a t.me link back to the original channel post.
link_back = _flag('link_back', False)

# --- bundling ---------------------------------------------------------------
# Album members arrive back to back; a short debounce is enough to collect them.
album_debounce = 3  # seconds
# How long a media-only post waits for its caption to arrive as a separate
# message before giving up and going out without one.
text_wait = 120  # seconds
# A lone text post still waits briefly, so a quick correction can replace it.
text_debounce = 3  # seconds

# --- approval ---------------------------------------------------------------
approve_timeout = 300  # seconds, then the prompt expires

# --- deletion ---------------------------------------------------------------
# The delete events are only a latency optimisation; this sweep is the guarantee.
reconcile_interval = 600  # seconds
reconcile_batch = 100  # ids per get_messages call

# --- X limits ---------------------------------------------------------------
max_media = 4
max_weighted_len = 280
