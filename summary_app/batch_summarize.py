from typing import List
import asyncio
import openai
from loguru import logger

from youtube import PhraseBlock

MAX_BATCHS = 10


def approx_sentences(chunk):
    import re

    sentences = re.split(r' *[\.\?!][\'"\)\]]* *', chunk)
    if len(sentences) == 1:
        return chunk[0], ""
    *rest, tail = sentences[:-1]
    # the last part may be incomplete so we keep it for the next batch
    return " ".join(rest), tail


async def generate_batchs(
    transcript: List[PhraseBlock], char_chunk=5000, max_batchs=MAX_BATCHS
):
    """
    Given a list of PhraseBlock, generate a batch of text to be sent to summarization.

    Returns:
    --------
    start_time: float
        The start time of the first phrase in the batch
    batch: str
        The text to be sent to summarization
    """
    batchs = 0
    start_time = 0
    acc_tokens = ""
    async for phrase in transcript:
        phrase = PhraseBlock(phrase.start, phrase.text)
        acc_tokens += " " + phrase.text.strip().replace("\n", " ")
        if len(acc_tokens) > char_chunk:
            batch, tail = approx_sentences(acc_tokens)
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
You are a writer tasked with summarizing the piece of the transcript for a video h
ere is a part of the transcript, make sure to match the tone of the vide:

Video:
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
            yield chunk["choices"][0]["text"]

    return gen()


async def stream_summaries_from_text(blocks, open_api_key=None):
    # this is an async generator that yields summaries blocks as they are generated
    completion = await asyncio.gather(
        *[summarize(block, openai_api_key=open_api_key) async for block in blocks]
    )
    for resp in completion:
        async for cr in resp:
            yield cr
