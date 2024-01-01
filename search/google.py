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


def get_google_results(html: str, num: int = 3) -> list[Tag]:
    soup = BeautifulSoup(html, 'html.parser')
    main = soup.find('div', id='main')
    search = main.find('div', id='search')
    rso = search.find('div', id='rso')
    divs = []
    data_div = rso.find('g-card-section')
    if data_div:
        divs.append(data_div)
    overview = rso.find('div', attrs={'id': 'kp-wp-tab-overview'})
    if overview:
        divs.extend(overview.find_all('div', recursive=False))
    else:
        divs.extend(rso.find_all('div', recursive=False))
    return divs[:num]


def has_google_organic_result(first_div: Tag) -> bool:
    has_feedback_button = False
    for span in first_div.find_all('span'):
        if FEEDBACK_SPAN_CLASS in span.attrs.get('class', []):
            has_feedback_button = True
            break
    return has_feedback_button


def google_knowledge_card(html: str) -> str:
    soup = BeautifulSoup(html, 'html.parser')
    main = soup.find('div', id='main')
    complementary = main.find('div', id='rhs')
    if complementary:
        return tag_to_text(complementary)
    return ''


def get_google_final_result(html: str, num: int = 3) -> str:
    google_results = get_google_results(html, num)
    has_organic_result = has_google_organic_result(google_results[0])
    knowledge_card = google_knowledge_card(html)
    results_text = [tag_to_text(div) for div in google_results]
    if knowledge_card:
        if has_organic_result:
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
