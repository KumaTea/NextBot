import aiohttp
from bs4 import BeautifulSoup
from common.data import USER_AGENT
from bot.session import config, logging
from search.tools import trim_result_text


async def baidu_search_raw(query: str) -> str:
    async with aiohttp.ClientSession() as session:
        async with session.get(
            'https://www.baidu.com/s',
            params={'wd': query},
            headers={'User-Agent': USER_AGENT, 'Cookie': config['cookie']['baidu']},
        ) as resp:
            return await resp.text()


def first_baidu_result(html: str) -> str:
    soup = BeautifulSoup(html, 'html.parser')
    results = soup.find('div', id='content_left')
    if not results:
        return ''
    first_result = results.find('div', id='1')
    result = first_result.get_text()
    result = trim_result_text(result)
    return result


async def baidu_search(query: str) -> str:
    html = await baidu_search_raw(query)
    result = first_baidu_result(html)
    if not result:
        logging.warning(f'[baidu] No results found for {query}')
    return result
