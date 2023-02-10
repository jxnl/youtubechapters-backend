import asyncio
from typing import AsyncGenerator, Iterable, List, Tuple
import openai
from loguru import logger

from phrase_block import PhraseBlock

MAX_BATCHS = 10


def approx_sentences(chunk: str) -> Tuple[str, str]:
    import re

    sentences = re.split(r' *[\.\?!][\'"\)\]]* *', chunk)
    if len(sentences) == 1:
        return chunk, ""
    *rest, tail = sentences[:-1]
    # the last part may be incomplete so we keep it for the next batch
    return " ".join(rest), tail


async def merge_phrases(
    transcript: AsyncGenerator[PhraseBlock, None],
    max_batchs=MAX_BATCHS,
) -> AsyncGenerator[PhraseBlock, None]:
    # this function merges phrases into batches of a certain size
    # Example: ["hello", "world", "this", "is", "a", "test"] -> ["hello world this",  "is a "test"]
    # this is useful since we can batch summarize the text in chunks
    batchs = 0
    start_time = 0
    acc_tokens = ""

    async for phrase in transcript:
        acc_tokens += " " + phrase.text.strip().replace("\n", " ")

        if not phrase.from_whisper:
            # it just means we probs have everything already
            # so we can just yield the whole thing
            chunk = 4000
        else:
            # this helps show stuff sooner since summarizing
            # and rendering buys us time.
            chunk = [300, 600, 1200, 3000, 5000][batchs if batchs < 5 else -1]

        if len(acc_tokens) > chunk:
            batch, tail = approx_sentences(acc_tokens)
            logger.info(f"Yielding big batch {batch}")
            yield PhraseBlock(start_time, batch)
            batchs += 1
            acc_tokens = tail
            start_time = phrase.start
        if batchs >= max_batchs:
            # safety check
            logger.info("Reached max batchs")
            yield PhraseBlock(start_time, batch)
            break
    yield PhraseBlock(start_time, acc_tokens)


PROMPT = """
Summarize the following content, only state the facts.

Content:
{text} 

Overview:
"""


async def summarize(block: PhraseBlock, openai_api_key=None, engine="text-davinci-003"):
    """
    Summarize a text using OpenAI. This is a generator that yields
    the summaries as they are generated.
    """
    logger.info(f"Summarizing text with OpenAI of length: {len(block.text)}")
    if openai_api_key is not None:
        openai.api_key = openai_api_key
    # Create a completion generator
    response = await openai.Completion.acreate(
        engine=engine,
        prompt=PROMPT.format(text=block.text),
        stream=True,
        max_tokens=1000,
        temperature=0,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0.6,
    )

    # Create a generator that yields the choices as they are generated
    # here we would just return and forward the entire openai response
    # but its more data and dont think its needed
    async def gen():
        async for chunk in response:
            yield PhraseBlock(start=block.start, text=chunk["choices"][0]["text"])

    return gen()


async def stream_summaries_from_text(
    blocks: AsyncGenerator[PhraseBlock, None], open_api_key=None
) -> AsyncGenerator[PhraseBlock, None]:
    # this is an async generator that yields summaries blocks as they are generated
    async for block in blocks:
        async for summary in await summarize(block, openai_api_key=open_api_key):
            yield summary
