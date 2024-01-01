import aiohttp
from bot.session import logging
from bs4 import BeautifulSoup, Tag
from common.data import USER_AGENT
from search.tools import tag_to_text


FEEDBACK_SPAN_CLASS = 'W7GCoc'


async def google_search_raw(query: str) -> str:
    async with aiohttp.ClientSession() as session:
        async with session.get(
            'https://www.google.com/search',
            params={'q': query},
            headers={'User-Agent': USER_AGENT},
        ) as resp:
            return await resp.text()


def first_google_result_div(html: str) -> Tag:
    soup = BeautifulSoup(html, 'html.parser')
    main = soup.find('div', id='main')
    search = main.find('div', id='search')
    rso = search.find('div', id='rso')
    first_div = rso.find('div')
    return first_div


def first_google_result(first_div: Tag) -> str:
    return tag_to_text(first_div)


def get_google_results(html: str, num: int = 3) -> list[Tag]:
    soup = BeautifulSoup(html, 'html.parser')
    main = soup.find('div', id='main')
    search = main.find('div', id='search')
    rso = search.find('div', id='rso')
    divs = rso.find_all('div', recursive=False)
    return divs[:num]


def google_organic_result(first_div: Tag) -> str:
    has_feedback_button = False
    for span in first_div.find_all('span'):
        if FEEDBACK_SPAN_CLASS in span.attrs.get('class', []):
            has_feedback_button = True
            break
    if has_feedback_button:
        return first_google_result(first_div)
    return ''


def google_knowledge_card(html: str) -> str:
    soup = BeautifulSoup(html, 'html.parser')
    main = soup.find('div', id='main')
    knowledge_card = main.find('div', class_='kp-wholepage')
    if not knowledge_card:
        return ''
    result = tag_to_text(knowledge_card)
    return result


def get_google_final_result(html: str, num: int = 3) -> str:
    first_div = first_google_result_div(html)
    organic_result = google_organic_result(first_div)
    knowledge_card = google_knowledge_card(html)
    google_results = get_google_results(html, num)
    results_text = [tag_to_text(div) for div in google_results]
    if knowledge_card:
        if organic_result:
            results_text.insert(1, knowledge_card)
        else:
            results_text.insert(0, knowledge_card)
    return '\n\n'.join(results_text[:num])


async def google_search(query: str, num: int = 3) -> str:
    html = await google_search_raw(query)
    result = get_google_final_result(html, num)
    if not result:
        logging.warning(f'[google] No results found for {query}')
    return result
