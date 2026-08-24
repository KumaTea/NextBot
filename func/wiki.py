import re
import asyncio
import aiohttp
import logging
from bs4 import BeautifulSoup
from datetime import datetime
from urllib.parse import quote
from dataclasses import dataclass
from share.auth import ensure_auth
from gpt.tools import trim_command
from telethon.tl.custom import Message


@dataclass
class Wiki:
    items: list[str]
    fetch_time: datetime


KumaPedia = Wiki([], datetime.now())
SITEMAP_URL = 'https://wiki.kmtea.eu/start?do=index'

symbol_pattern = re.compile(r'[!@#$%^&*()_+={}\[\]:;"\'<>,.?/\|`~]')


async def aget(url: str) -> tuple[str, int]:
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            return await resp.text(), resp.status


async def fetch_wiki():
    html, _ = await aget(SITEMAP_URL)

    # find all <a> tags with class="wikilink1" and extract the title
    soup = BeautifulSoup(html, 'html.parser')
    items = [a['title'] for a in soup.find_all('a', class_='wikilink1')]
    items = [item.lower().replace('_', ' ') for item in items]
    items = list(set(items))

    KumaPedia.items = items
    KumaPedia.fetch_time = datetime.now()

    logging.info(f'[func_wiki]\tFetched {len(items)} items from KumaPedia')
    return items


@ensure_auth
async def command_wiki(event) -> Message:
    query = trim_command(event.raw_text or '')
    if not query:
        return await event.reply('请输入要查询的关键字')

    kuma_query = symbol_pattern.sub(' ', query.lower())
    kuma_quoted_query = kuma_query.replace(' ', '_')

    # wiki is fetched at start time
    if kuma_query in KumaPedia.items:
        return await event.respond(
            f'[kuma]: <a href="https://wiki.kmtea.eu/{kuma_quoted_query}">{query}</a>',
            parse_mode='html'
        )

    inform = await event.respond('正在查询……')

    quoted_query = quote(query)
    zh_wiki_url = f'https://zh.wikipedia.org/zh-cn/{quoted_query}'
    en_wiki_url = f'https://en.wikipedia.org/wiki/{quoted_query}'

    zh_wiki, en_wiki = await asyncio.gather(
        aget(zh_wiki_url),
        aget(en_wiki_url)
    )

    if zh_wiki[1] == 200:
        return await inform.edit(
            f'[zhwp]: <a href="{zh_wiki_url}">{query}</a>',
            parse_mode='html'
        )
    if en_wiki[1] == 200:
        return await inform.edit(
            f'[enwp]: <a href="{en_wiki_url}">{query}</a>',
            parse_mode='html'
        )

    return await inform.edit('未找到相关条目 😢')
