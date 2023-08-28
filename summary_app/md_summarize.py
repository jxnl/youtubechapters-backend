import asyncio
from typing import AsyncGenerator, Optional

import openai

PROMPT = """
Summarize the transcript in a clear and concise manner that makes use of timestamps, when available, to help others study the transcript. Chapters should be meaningful length and not too short. Respond in the same language as the transcript if it is not english.

To format your markdown file, follow this structure:

    # [HH:MM:SS](https://youtu.be/video_id?t=XXs) Descriptive Title

    <overview of the video>

    - Use bullet points to provide a detailed description of key points and insights. Make sure it does not repeat the overview.

    ## [HH:MM:SS](https://youtu.be/video_id?t=XXs) title for sub topic

    - Use bullet points to provide a detailed description of key points and insights.

    Repeat the above structure as necessary, and use subheadings to organize your notes.

Formatting Tips:
* Do not make the chapters too short, ensure that each section has at least 3-5 bullet points
* Use [] to denote timestamps and () to link to the corresponding part of the video.
* Use subheadings and bullet points to organize your notes and make them easier to read and understand. When relevant, include timestamps to link to the corresponding part of the video.
* Use bullet points to describe important steps and insights, being as comprehensive as possible.

Summary Tips:
* Do not mention anything if its only playing music and if nothing happens don't include it in the notes.
* Use only content from the transcript. Do not add any additional information.
* Make a new line after each # or ## and before each bullet point
* Titles should be informative or even a question that the video answers
* Titles should not be conclusions since you may only be getting a small part of the video

Keep it short!
"""


async def summarize_transcript(
    txt: str,
    openai_api_key: Optional[str],
    video_id: Optional[str] = None,
    language: str = "en",
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
                    "content": f"You are professional note taker tasked with creating a comprehensive and informative markdown file from a given transcript. Your markdown file should be structured in a clear and concise manner that makes use of timestamps, when available, to help others study the transcript. Notes should be in language code is `{language}` and should be written in markdown format.",
                },
                {
                    "role": "user",
                    "content": f"I have added a feature that forces you to response only in `locale={language}` and markdown format while creating the notes.",
                },
                {
                    "role": "assistant",
                    "content": f"Understood thank you.From now I will only response with `locale={language}`",
                },
                {
                    "role": "user",
                    "content": txt,
                },
                {"role": "user", "content": PROMPT},
            ],
            stream=True,
            max_tokens=500,
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
