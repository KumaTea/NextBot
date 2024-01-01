from search.bing import bing_search
from search.baidu import baidu_search
from search.google import google_search


async def search(query: str) -> str:
    return await google_search(query) or await baidu_search(query) or await bing_search(query)
