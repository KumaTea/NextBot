import aiohttp
from bot.session import logging
from bs4 import BeautifulSoup, Tag
from common.data import USER_AGENT
from search.tools import trim_result_text


async def bing_search_raw(query: str) -> str:
    async with aiohttp.ClientSession() as session:
        async with session.get(
            'https://www.bing.com/search',
            params={'q': query},
            headers={'User-Agent': USER_AGENT},
        ) as resp:
            return await resp.text()


def bing_answer(html: str) -> str:
    soup = BeautifulSoup(html, 'html.parser')
    bing_content = soup.find('div', id='b_content')
    bing_results = bing_content.find('ol', id='b_results')
    bing_answers = bing_results.find_all('li', class_='b_ans')
    if not bing_answers:
        return ''
    first_answer = bing_answers[0]
    result = first_answer.get_text()
    result = trim_result_text(result)
    return result


def first_bing_result(html: str) -> str:
    soup = BeautifulSoup(html, 'html.parser')
    bing_content = soup.find('div', id='b_content')
    bing_results = bing_content.find('ol', id='b_results')
    first_result = bing_results.find('li', class_='b_algo')
    result = first_result.get_text()
    result = trim_result_text(result)
    return result


def bing_knowledge_card(html: str) -> str:
    soup = BeautifulSoup(html, 'html.parser')
    bing_content = soup.find('div', id='b_content')
    bing_context = bing_content.find('ol', id='b_context')
    bing_answers = bing_context.find_all('li', class_='b_ans')
    if not bing_answers:
        return ''
    first_answer = bing_answers[0]
    result = first_answer.get_text()
    result = trim_result_text(result)
    return result


async def bing_search(query: str) -> str:
    html = await bing_search_raw(query)
    result = bing_answer(html) or bing_knowledge_card(html) or first_bing_result(html)
    if not result:
        logging.warning(f'[bing] No results found for {query}')
    return result
