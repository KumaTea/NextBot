from bot.session import gpt
from typing import AsyncGenerator
from common.info import gpt_model


periods = [
    ', ', '，',
    '. ', '。',
    '! ', '！',
    '? ', '？',
]


async def stream_chat(messages: list, model: str = gpt_model) -> AsyncGenerator[str, None]:
    """
    This function yield chunks, not full message!
    """
    async for chunk in await gpt.chat.completions.create(
        model=model,
        messages=messages,
        stream=True
    ):
        # ref: https://til.simonwillison.net/gpt3/python-chatgpt-streaming-api
        content = chunk.choices[0].delta.content
        if content:
            yield content


async def stream_chat_by_sentences(messages: list, model: str = gpt_model) -> AsyncGenerator[str, None]:
    """
    This function yield chunks by sentences, not full message!
    """
    text = ''
    async for chunk in stream_chat(messages, model):
        text += chunk
        if len(text) > 1 and any([text.endswith(i) for i in periods]):
            yield text
            text = ''
    if text:
        yield text
