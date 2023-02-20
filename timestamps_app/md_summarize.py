import asyncio
import os
from typing import AsyncGenerator, Optional

import promptlayer

promptlayer.api_key = os.environ.get("PROMPTLAYER_KEY")

# Swap out your 'import openai'
openai = promptlayer.openai

PROMPT = """
You are a professional note taker tasked with creating a comprehensive and informative markdown file from a given transcript. Your markdown file should be structured in a clear and concise manner that makes use of timestamps, when available, to help others study the transcript. Your job is to summarize the content of the transcript as accurately and succinctly as possible.

To format your markdown file, follow this structure:

    # [HH:MM:SS](https://youtu.be/video_id?t=XXs) Descriptive Title

    Overview: ...

    **title for sub topic **

    Use bullet points to provide a detailed description of key points and insights.

    # [HH:MM:SS](https://youtu.be/video_id?t=XXs) Descriptive Title

    Repeat the above structure as necessary, and use subheadings to organize your notes.

Some tips to keep in mind:

* Use only content from the given transcript, without adding any additional information.
* Pay close attention to the speaker's key points and take thorough notes.
* Use subheadings and bullet points to organize your notes and make them easier to read and understand. When relevant, include timestamps to link to the corresponding part of the video.
* Create descriptive titles that accurately reflect the content of each section.
* Highlight any memorable phrases or quotes to aid recall or as evidence.
* Use bullet points to describe important steps and insights, being as comprehensive as possible.
* Avoid repeating yourself in either the content or the timestamp.
* Cite and include timestamps whenever possible by linking to the relevant URL in a block.
Content:

{text} 

Study Guide:
"""


async def summarize_transcript(
    txt: str,
    openai_api_key: Optional[str],
    semaphore: Optional[asyncio.Semaphore] = None,
    engine: str = "text-davinci-003",
):
    if openai_api_key is not None:
        openai.api_key = openai_api_key

    async def call() -> AsyncGenerator[str, None]:
        response = await openai.Completion.acreate(
            engine=engine,
            prompt=PROMPT.format(text=txt),
            stream=True,
            max_tokens=1000,
            temperature=0,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0.6,
            pl_tags=["youtube_summary"],
        )

        async def gen():
            async for chunk in response:  # type: ignore
                yield chunk["choices"][0]["text"]
            yield "\n"

        return gen()

    if semaphore is None:
        return await call()

    async with semaphore:
        return await call()
