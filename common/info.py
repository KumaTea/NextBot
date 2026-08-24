import os

version = '4.2.3.496'
channel = 'local' if os.name == 'nt' else 'cloud'
username = 'rbskbot'

self_id = 6307401083
old_kuma_id = 345060487
kuma_id = 5273618487

administrators = {old_kuma_id, kuma_id}
gpt_admins = administrators

# --- channel -> X mirror ----------------------------------------------------
# Fixed, so they are spelled out here rather than in config.ini.
sync_channel_id = -1001525690242  # @KumaSpace
sync_channel_name = 'KumaSpace'
# The channel's linked discussion group. The bot sits here for two reasons:
# approval prompts thread under the auto-forwarded copy, and deleting a channel
# post deletes that copy too -- a delete signal bots do reliably receive.
sync_group_id = -1001932978232  # @teasps
# Checked against the account the cookies actually belong to before publishing.
x_user_id = 3703623798  # @KumaTea0
x_username = 'KumaTea0'

max_dialog = 10  # conversations
max_chunk = 25  # characters
min_edit_interval = 5  # seconds
max_voice_len = 60  # seconds, for the automatic reaction
max_transcribe_len = 30 * 60  # seconds, for an explicitly asked /transcribe

gpt_model = 'gemini-3.1-flash-lite-preview'
reasoning_model = 'gemini-3.1-flash-lite-preview'  # gemini-3-pro-preview has no free tier
