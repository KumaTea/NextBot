import aiohttp
from bot.session import logging
from bs4 import BeautifulSoup, Tag
from common.data import USER_AGENT
from search.tools import trim_result_text


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
    result = first_div.get_text()
    result = trim_result_text(result)
    return result


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
    result = knowledge_card.get_text()
    result = trim_result_text(result)
    return result


async def google_search(query: str) -> str:
    html = await google_search_raw(query)
    first_div = first_google_result_div(html)
    result = google_organic_result(first_div) or google_knowledge_card(html) or first_google_result(first_div)
    if not result:
        logging.warning(f'[google] No results found for {query}')
    return result
