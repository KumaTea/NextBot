import re
import asyncio
import aiohttp
import logging
from pyrogram import Client
from bs4 import BeautifulSoup
from datetime import datetime
from dataclasses import dataclass
from pyrogram.types import Message
from share.auth import ensure_auth
from gpt.tools import trim_command
from pyrogram.enums.parse_mode import ParseMode


@dataclass
class Wiki:
    items: list[str]
    fetch_time: datetime


KumaPedia = Wiki([], datetime.now())
SITEMAP_URL = 'https://wiki.kmtea.eu/start?do=index'

symbol_pattern = re.compile(r'[!@#$%^&*()_+={}\[\]:;"\'<>,.?/\\|`~]')


async def aget(url: str) -> tuple[str, int]:
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            return await resp.text(), resp.status


async def fetch_wiki():
    html, _ = await aget(SITEMAP_URL)

    # find all <a> tags with class="wikilink1" and extract the title
    soup = BeautifulSoup(html, 'html.parser')
    items = [a['title'] for a in soup.find_all('a', class_='wikilink1')]
    items = [item.lower() for item in items]
    items = [item.replace('_', ' ') for item in items]
    items = list(set(items))

    KumaPedia.items = items
    KumaPedia.fetch_time = datetime.now()

    logging.info(f'[func_wiki]\tFetched {len(items)} items from KumaPedia')
    return items


@ensure_auth
async def command_wiki(client: Client, message: Message) -> Message:
    text = message.text
    query = trim_command(text)
    if not query:
        return await message.reply_text('请输入要查询的关键字')

    query = query.lower()
    query = symbol_pattern.sub(' ', query)

    # wiki is fetched at start time
    if query.lower() in KumaPedia.items:
        # return await message.reply_text(f'\\[kuma]: [{query}](https://wiki.kmtea.eu/{query})', quote=False)
        return await message.reply_text(
            f'[kuma]: <a href="https://wiki.kmtea.eu/{query}">{query}</a>',
            parse_mode=ParseMode.HTML,
            quote=False
        )

    inform = await message.reply_text('正在查询……', quote=False)

    zh_wiki_url = f'https://zh.wikipedia.org/zh-cn/{query}'
    en_wiki_url = f'https://en.wikipedia.org/wiki/{query}'

    zh_wiki, en_wiki = await asyncio.gather(
        aget(zh_wiki_url),
        aget(en_wiki_url)
    )

    if zh_wiki[1] == 200:
        return await inform.edit_text(
            f'[zhwp]: <a href="{zh_wiki_url}">{query}</a>',
            parse_mode=ParseMode.HTML
        )
    if en_wiki[1] == 200:
        return await inform.edit_text(
            f'[enwp]: <a href="{en_wiki_url}">{query}</a>',
            parse_mode=ParseMode.HTML
        )

    return await inform.edit_text('未找到相关条目 😢')
