"""Turning a Telegram post into something X will accept.

X does not count characters, it counts *weighted* length: the ranges below
weigh 1, everything else -- CJK, emoji -- weighs 2, and the cap is 280. That is
where the familiar "140 Chinese characters" figure comes from, so this measures
the real thing instead of guessing at the language. Links always count as 23,
however long they are, because X rewrites them to t.co.

Reference: the twitter-text v3 configuration.
"""

import re
from common.data import url_regex
from common.info import sync_channel_name
from x.config import max_weighted_len


url_pattern = re.compile(url_regex)

# Codepoint ranges that weigh 1 instead of 2 (latin, cyrillic, greek, hebrew,
# arabic, plus a few punctuation blocks). Everything outside them weighs 2.
light_ranges = (
    (0x0000, 0x10FF),
    (0x2000, 0x200D),
    (0x2010, 0x201F),
    (0x2032, 0x2037),
)

url_weight = 23

# A post longer than the cap is cut at the first of these. Extend the set here
# if you ever want '!' or '?' to end a tweet too.
boundaries = ('.', '。', '\n')

ellipsis = '…'

# Pieces that continue an emoji cluster rather than starting a new one.
zwj = '‍'
variation_selector = '️'
keycap = '⃣'
skin_tones = range(0x1F3FB, 0x1F400)
regional_indicators = range(0x1F1E6, 0x1F200)


def _char_weight(char: str) -> int:
    point = ord(char)
    for start, end in light_ranges:
        if start <= point <= end:
            return 1
    return 2


def _clusters(text: str) -> list[str]:
    """
    Split into what X counts as one unit.

    An emoji built out of several codepoints -- a flag, a skin tone, a ZWJ
    family -- is one unit weighing 2, not one unit per codepoint. Without this
    a single family emoji would score 8.
    """
    out = []
    i = 0
    while i < len(text):
        start = i
        i += 1
        # a flag is exactly two regional indicators
        if ord(text[start]) in regional_indicators:
            if i < len(text) and ord(text[i]) in regional_indicators:
                i += 1
            out.append(text[start:i])
            continue
        # trailing modifiers, then any number of ZWJ-joined continuations
        while i < len(text):
            point = ord(text[i])
            if text[i] in (variation_selector, keycap) or point in skin_tones:
                i += 1
            elif text[i] == zwj and i + 1 < len(text):
                i += 2
            else:
                break
        out.append(text[start:i])
    return out


def weighted_len(text: str) -> int:
    """How long X considers this text to be."""
    if not text:
        return 0

    total = 0
    cursor = 0
    for match in url_pattern.finditer(text):
        total += _weigh_plain(text[cursor:match.start()])
        total += url_weight
        cursor = match.end()
    total += _weigh_plain(text[cursor:])
    return total


def _weigh_plain(text: str) -> int:
    return sum(
        max(_char_weight(c) for c in cluster)
        for cluster in _clusters(text)
    )


def _longest_prefix(text: str, limit: int) -> str:
    """The longest leading slice of `text` that still fits in `limit`."""
    total = 0
    kept = 0
    cursor = 0
    # walk URLs and plain runs in order so a link is never cut in half
    spans = []
    for match in url_pattern.finditer(text):
        if match.start() > cursor:
            spans.append((text[cursor:match.start()], False))
        spans.append((match.group(), True))
        cursor = match.end()
    if cursor < len(text):
        spans.append((text[cursor:], False))

    for span, is_url in spans:
        if is_url:
            if total + url_weight > limit:
                return text[:kept]
            total += url_weight
            kept += len(span)
            continue
        for cluster in _clusters(span):
            weight = max(_char_weight(c) for c in cluster)
            if total + weight > limit:
                return text[:kept]
            total += weight
            kept += len(cluster)
    return text[:kept]


def fit(text: str, limit: int = None) -> str:
    """
    Shorten a post to something X will take.

    Within the cap the text goes out untouched. Over it, the post is cut at the
    *first* sentence boundary that fits -- the opening sentence stands in for
    the whole post -- and only when there is no such boundary does it get cut
    mid-sentence with an ellipsis.
    """
    limit = max_weighted_len if limit is None else limit
    text = (text or '').strip()
    if weighted_len(text) <= limit:
        return text

    first = min(
        (pos for pos in (text.find(b) for b in boundaries) if pos > 0),
        default=-1
    )
    if first > 0:
        # keep '.'/'。' as part of the sentence, drop a newline
        cut = text[:first + 1] if text[first] != '\n' else text[:first]
        cut = cut.strip()
        if cut and weighted_len(cut) <= limit:
            return cut

    # no usable boundary -- reserve room for the ellipsis (which is itself a
    # weight-2 character) and cut mid-sentence
    return _longest_prefix(text, limit - weighted_len(ellipsis)).rstrip() + ellipsis


def channel_link(message_id: int) -> str:
    return f'https://t.me/{sync_channel_name}/{message_id}'


def render(text: str, message_id: int = 0, with_link: bool = False) -> str:
    """The final tweet body for a channel post."""
    text = (text or '').strip()
    if not (with_link and message_id):
        return fit(text)

    link = channel_link(message_id)
    # the link has to survive the cut, so shorten the body around it
    room = max_weighted_len - url_weight - 1  # -1 for the newline
    body = text if weighted_len(text) <= room else fit_to(text, room)
    return f'{body}\n{link}'.strip()


def fit_to(text: str, limit: int) -> str:
    """`fit`, against a caller-supplied cap rather than X's own."""
    global max_weighted_len
    original = max_weighted_len
    try:
        max_weighted_len = limit
        return fit(text)
    finally:
        max_weighted_len = original
