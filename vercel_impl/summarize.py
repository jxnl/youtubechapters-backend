from typing import AsyncGenerator
from loguru import logger

import openai

from phrase_block import PhraseBlock

MAX_BATCHS = 10
CHUNK_SIZE = 6000


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

        if len(acc_tokens) > CHUNK_SIZE:
            # batch, tail = approx_sentences(acc_tokens)
            batch = acc_tokens  #
            logger.info(f"{len(acc_tokens)}, {batch}")
            yield PhraseBlock(start=start_time, end=phrase.end, text=batch)
            batchs += 1
            start_time = phrase.start
        if batchs >= max_batchs:
            # safety check
            logger.info("Reached max batchs")
            yield PhraseBlock(start=start_time, end=phrase.end, text=batch)
            break
    yield PhraseBlock(start=start_time, end=phrase.end, text=batch)


PROMPT = """
Summarize the following content, only include information from the content and state the facts.
the content comes from a transcription anything looks like a transcription error, throw it out.

Content:
{text} 

Summary:
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
            yield PhraseBlock(
                start=block.start, end=block.end, text=chunk["choices"][0]["text"]
            )

    return gen()


async def stream_summaries_from_text(
    blocks: AsyncGenerator[PhraseBlock, None], open_api_key=None
) -> AsyncGenerator[PhraseBlock, None]:
    # this is an async generator that yields summaries blocks as they are generated
    async for block in blocks:
        async for summary in await summarize(block, openai_api_key=open_api_key):
            yield summary
        # yield a space to separate the summaries otherwise we will end `end.start` `
        yield PhraseBlock(start=block.end, end=block.end, text=" ")
