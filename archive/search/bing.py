import aiohttp
from bot.session import logging
from share.data import USER_AGENT
from bs4 import Tag, BeautifulSoup
from search.tools import tag_to_text


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
    bing_answers = bing_results.find_all('li', class_='b_ans', recursive=False)
    if not bing_answers:
        return ''
    first_answer = bing_answers[0]
    result = tag_to_text(first_answer)
    return result


def get_bing_results(html: str, num: int = 3) -> list[Tag]:
    soup = BeautifulSoup(html, 'html.parser')
    bing_content = soup.find('div', id='b_content')
    bing_results = bing_content.find('ol', id='b_results')
    results = bing_results.find_all('li', class_='b_algo', recursive=False)
    return results[:num]


def bing_knowledge_card(html: str) -> str:
    soup = BeautifulSoup(html, 'html.parser')
    bing_content = soup.find('div', id='b_content')
    bing_context = bing_content.find('ol', id='b_context')
    bing_answers = bing_context.find_all('li', class_='b_ans', recursive=False)
    if not bing_answers:
        return ''
    first_answer = bing_answers[0]
    result = tag_to_text(first_answer)
    return result


def get_bing_final_result(html: str, num: int = 3) -> str:
    answer = bing_answer(html)
    knowledge_card = bing_knowledge_card(html)
    bing_results = get_bing_results(html, num)
    results_text = [tag_to_text(div) for div in bing_results]
    if knowledge_card:
        if answer:
            results_text.insert(1, knowledge_card)
        else:
            results_text.insert(0, knowledge_card)
    return '\n\n'.join(results_text[:num])


async def bing_search(query: str, num: int = 3) -> str:
    html = await bing_search_raw(query)
    result = get_bing_final_result(html, num)
    if not result:
        logging.warning(f'[bing] No results found for {query}')
    return result
