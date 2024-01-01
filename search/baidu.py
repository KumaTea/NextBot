import aiohttp
from bs4 import BeautifulSoup, Tag
from common.data import USER_AGENT
from search.tools import tag_to_text
from bot.session import config, logging


async def baidu_search_raw(query: str) -> str:
    async with aiohttp.ClientSession() as session:
        async with session.get(
            'https://www.baidu.com/s',
            params={'wd': query},
            headers={'User-Agent': USER_AGENT, 'Cookie': config['cookies']['baidu']},
        ) as resp:
            return await resp.text()


def get_baidu_results(html: str, num: int = 3) -> list[Tag]:
    soup = BeautifulSoup(html, 'html.parser')
    results = soup.find('div', id='content_left')
    if not results:
        return []
    divs = results.find_all('div', recursive=False)
    return divs[:num]


async def baidu_search(query: str, num: int = 3) -> str:
    html = await baidu_search_raw(query)
    result = '\n\n'.join(tag_to_text(div) for div in get_baidu_results(html, num))
    if not result:
        logging.warning(f'[baidu] No results found for {query}')
    return result
