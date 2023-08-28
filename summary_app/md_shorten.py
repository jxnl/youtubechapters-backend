import asyncio
from typing import AsyncGenerator, Optional

import openai

PROMPT = """
You are a professional note taker tasked with shortening and organizing a study guide.
Your markdown file should be structured in a clear and concise manner that makes use of timestamps, when available, to help others study the transcript. 

To format your markdown file, follow this structure:

    # [HH:MM:SS](https://youtu.be/video_id?t=XXs) Descriptive Title

    Summary: ...

    Use bullet points to provide a informative description of key points and insights.

    # [HH:MM:SS](https://youtu.be/video_id?t=XXs) Descriptive Title

    Repeat the above structure as necessary, and use subheadings to organize your notes.

Some tips to keep in mind:

* Use only content from the given transcript, without adding any additional information.
* Highlight any memorable phrases or quotes to aid recall or as evidence.
* Use bullet points to describe important steps and insights, being as comprehensive as possible.
* Avoid repeating yourself in either the content or the timestamp.

Study Guide:

{text} 

Shortened Study Guide:
"""


async def shorten_md(
    txt: str,
    openai_api_key: Optional[str],
    semaphore: Optional[asyncio.Semaphore] = None,
):
    if openai_api_key is not None:
        openai.api_key = openai_api_key

    async def call() -> AsyncGenerator[str, None]:
        response = await openai.ChatCompletion.acreate(
            model="gpt-3.5-turbo-16k",
            messages=[
                {
                    "role": "system",
                    "content": "You are a professional note taker tasked with merging and shortening a study guide. Your markdown file should be structured in a clear and concise manner that makes use of timestamps, when available, to help others study.",
                },
                {"role": "user", "content": PROMPT.format(text=txt)},
            ],
            stream=True,
            max_tokens=2000,
            temperature=0,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0.6,
        )

        async def gen():
            async for chunk in response:  # type: ignore
                yield chunk["choices"][0]["delta"].get("content", "")
            yield "\n"

        return gen()

    if semaphore is None:
        return await call()

    async with semaphore:
        return await call()
