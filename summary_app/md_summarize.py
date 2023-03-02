import asyncio
from typing import AsyncGenerator, Optional

import openai

PROMPT = """
You are a professional note taker tasked with creating a comprehensive and informative markdown file from a given transcript. Your markdown file should be structured in a clear and concise manner that makes use of timestamps, when available, to help others study the transcript. Your job is to summarize the content of the transcript as accurately and succinctly as possible.

To format your markdown file, follow this structure:

    # [HH:MM:SS](https://youtu.be/video_id?t=XXs) Descriptive Title

    Overview: ...

    **title for sub topic **

    Use bullet points to provide a detailed description of key points and insights.

    Repeat the above structure as necessary, and use subheadings to organize your notes.

Some tips to keep in mind:

* Use [] to denote timestamps and () to link to the corresponding part of the video.
* Use subheadings and bullet points to organize your notes and make them easier to read and understand. When relevant, include timestamps to link to the corresponding part of the video.
* Create descriptive titles that accurately reflect the content of each section.
* Use bullet points to describe important steps and insights, being as comprehensive as possible.
* Avoid repeating yourself in either the content or the timestamp.
* Only create a new section when the topic changes. If the topic is related to the previous section, use a subheading instead.
* Do not mention anything if its only playing music and if nothing happens don't write anything.
* Only mention things that are important and relevant to the topic.
* Use only content from the transcript. Do not add any additional information.

Content:

{text} 
"""


async def summarize_transcript(
    txt: str,
    openai_api_key: Optional[str],
    semaphore: Optional[asyncio.Semaphore] = None,
):
    if openai_api_key is not None:
        openai.api_key = openai_api_key

    async def call() -> AsyncGenerator[str, None]:
        response = await openai.ChatCompletion.acreate(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                    "content": "You are a professional note taker tasked with creating a comprehensive and informative markdown file from a given transcript. Your markdown file should be structured in a clear and concise manner that makes use of timestamps, when available, to help others study the transcript. Your job is to summarize the content of the transcript as accurately and succinctly as possible.",
                },
                {"role": "user", "content": PROMPT.format(text=txt)},
            ],
            stream=True,
            max_tokens=2000,
            temperature=0,
            top_p=1,
            frequency_penalty=0.6,
            presence_penalty=0.6,
        )

        async def gen():
            async for chunk in response:  # type: ignore
                yield chunk["choices"][0]["delta"].get("content", "")
            yield "\n\n"

        return gen()

    if semaphore is None:
        return await call()

    async with semaphore:
        return await call()
