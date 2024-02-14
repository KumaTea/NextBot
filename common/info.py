import os

version = '3.0.3.340'
channel = 'local' if os.name == 'nt' else 'cloud'
username = 'rbskbot'

self_id = 6307401083
old_kuma_id = 345060487
kuma_id = 5273618487
rimus_id = 1753720065

administrators = [old_kuma_id, kuma_id]
gpt_admins = administrators + [rimus_id]

max_dialog = 10  # conversations
max_chunk = 25  # characters
min_edit_interval = 5  # seconds
max_voice = 60  # seconds

gpt_model = 'gpt-4-turbo-preview'
