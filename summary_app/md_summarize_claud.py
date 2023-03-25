import asyncio
import os
from typing import AsyncGenerator, Optional

import anthropic

client = anthropic.Client(os.environ["CLAUDE_KEY"])

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
* Titles should not be conclusions since you may only be getting a small part of the video
"""


async def summarize_transcript(
    txt: str,
    language: str = "en",
    semaphore: Optional[asyncio.Semaphore] = None,
    **kwargs,
):
    async def call() -> AsyncGenerator[str, None]:
        response = client.completion_stream(
            prompt=f"""{anthropic.HUMAN_PROMPT}
{PROMPT}
<language> {language} </language>
{txt}\n{anthropic.AI_PROMPT}""",
            stream=True,
            stop_sequences=[anthropic.HUMAN_PROMPT],
            model="claude-instant-v1.0",
            max_tokens_to_sample=1000,
        )

        async def gen():
            last_chunk = ""
            for chunk in response:  # type: ignore
                print(chunk["completion"].replace(last_chunk, ""))
                yield chunk["completion"].replace(last_chunk, "")
                last_chunk = chunk["completion"]
            yield "\n\n"

        return gen()

    if semaphore is None:
        return await call()

    async with semaphore:
        return await call()
