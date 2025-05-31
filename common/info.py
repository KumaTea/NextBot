import os

version = '4.1.1.455'
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

gpt_model = 'gemini-2.5-flash-preview-05-20'
reasoning_model = 'gemini-2.5-pro-preview-05-06'
