import asyncio
from typing import AsyncGenerator, Optional

import openai

PROMPT = """
You are a professional note taker and your job is to take this transcript and produce a comprehensive and informative markdown file for others to study. Your markdown file should make use of timestamps (when available) and clearly and concisely summarize the content of the transcript.

To format the markdown file, please follow this structure:

markdown:

    # [HH:MM:SS](https://youtu.be/video_id?t=XXs) Descriptive Title

    <A brief overview of the topic>

    **Subtitle**

    * Detailed description of key point 1, including any relevant information and insights.
    * Detailed description of key point 2, including any relevant information and insights.

    # [HH:MM:SS](https://youtu.be/video_id?t=XXs) Descriptive Title

    ... (this can be repeated as many times as necessary you are allowed to use subheadings)



Tips:

* Do not include any information that is not in the transcript.
* Pay attention to the key points the speaker is making and take notes as you go.
* You can organize your notes into subheadings or bullet points to make it easier to read and understand, use timestamps to link to the relevant part of the video)
* Titles should be descriptive. Avoid using 2-3 word titles.
* If there are certain phrases or quotes that stand out to you, highlight them in your notes. This can help you remember them later or use them as evidence
* Use bullet points for detailing important steps and insights. Be as detailed and comprehensive as possible.
* Avoid repeating yourself, in either the content or the timestamp.
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
