import os

version = '4.0.0.442'
channel = 'local' if os.name == 'nt' else 'cloud'
username = 'rbskbot'

self_id = 6307401083
old_kuma_id = 345060487
kuma_id = 5273618487

administrators = {old_kuma_id, kuma_id}
gpt_admins = administrators

max_dialog = 10  # conversations
max_chunk = 25  # characters
min_edit_interval = 5  # seconds
max_voice_len = 60  # seconds

gpt_model = 'deepseek-r1:7b'
reasoning_model = 'deepseek-r1:32b'
