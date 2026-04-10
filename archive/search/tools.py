import unicodedata
from bs4 import Tag


def trim_result_text(result: str) -> str:
    while '  ' in result:
        result = result.replace('  ', ' ')
    while '\n\n' in result:
        result = result.replace('\n\n', '\n')
    return result


def tag_to_text(tag: Tag) -> str:
    result = tag.get_text()
    result = unicodedata.normalize('NFKC', result)
    result = trim_result_text(result)
    return result
