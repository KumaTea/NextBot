def trim_result_text(result: str) -> str:
    while '  ' in result:
        result = result.replace('  ', ' ')
    while '\n\n' in result:
        result = result.replace('\n\n', '\n')
    return result
