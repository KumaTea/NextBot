import os

version = '1.0.4.43'
channel = 'local' if os.name == 'nt' else 'cloud'
username = 'rbskbot'

self_id = 6307401083
old_kuma_id = 345060487
kuma_id = 5273618487
rimus_id = 1753720065

administrators = [old_kuma_id, kuma_id]
gpt_admins = administrators + [rimus_id]

max_dialog = 10
max_chunk = 25
min_edit_interval = 5
