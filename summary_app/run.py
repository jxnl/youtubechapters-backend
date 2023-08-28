import asyncio
import json
import re
from dataclasses import dataclass
from typing import Optional

from fastapi import Header, Request
from fastapi.responses import StreamingResponse
from loguru import logger
from schema import Summary
from segment import group_speech_segments, shorten_summary_to_md, summary_segments_to_md
from sqlalchemy.orm import Session
from sse_starlette import EventSourceResponse
from transcribe import transcribe_youtube


def extract_video_id(url: str) -> str:
    match = re.search(
        r"^(?:https?:\/\/)?(?:www\.)?(?:youtu\.be\/|youtube\.com\/(?:embed\/|v\/|watch\?v=|watch\?.+&v=))((\w|-){11})(?:\S+)?$",
        url,
    )
    if match:
        return match.group(1)
    else:
        raise ValueError("Invalid youtube url")


def async_generator_summary_timestamps(
    url: str,
    use_whisper: bool = False,
    openai_api_key: Optional[str] = None,
):
    video_id = extract_video_id(url)
    phrases = transcribe_youtube(video_id, use_whisper)
    phrases = group_speech_segments(phrases, max_length=300)
    phrases = summary_segments_to_md(
        phrases, openai_api_key=openai_api_key, video_id=video_id
    )
    return phrases


def async_generator_summary_shorten(content: str, openai_api_key):
    phrases = shorten_summary_to_md(content, openai_api_key=openai_api_key)
    return phrases


def open_ai_token_from_auth(auth):
    if auth is None or not auth.startswith("Bearer "):
        return None
    _, token = auth.split(" ")
    return token


def stream(
    generator,
    use_sse: bool,
    request: Request,
    data_fn=lambda x: x,
    url: Optional[str] = None,
):
    # this is a helper function to stream data from a generator in a fastapi endpoint
    # It handles both SSE and regular streaming responses and disconnects
    async def stream_obj():
        # this is a helper function to stream data from a generator

        # accumulate the summary markdown so we can save it to the db
        summary_markdown = ""
        try:
            async for obj in generator:
                if obj and not await request.is_disconnected():
                    data = data_fn(obj)

                    # accumulate the summary markdown so we can save it to the db
                    summary_markdown += data

                    # yield the data
                    yield {"data": json.dumps({"text": data})} if use_sse else str(data)

            # yield a done message
            if use_sse:
                yield {"data": "[DONE]"}
        except asyncio.CancelledError as e:
            logger.info(f"Streaming canceled.")
            raise e

    response = EventSourceResponse if use_sse else StreamingResponse
    return response(
        stream_obj(),  # type: ignore
        media_type="text/plain",
    )


@dataclass
class SummaryPayload:
    url: str
    use_sse: bool = False
    use_whisper: bool = False
    use_cache: bool = True


@dataclass
class ShortenPayload:
    content: str
    use_sse: bool = False


async def youtube_summary_md(
    req: SummaryPayload, request: Request, authorization: str = Header(None)
):
    token = open_ai_token_from_auth(authorization)
    async_generator = async_generator_summary_timestamps(
        url=req.url,
        use_whisper=req.use_whisper,
        openai_api_key=token,
    )
    return stream(
        async_generator, req.use_sse, request, data_fn=lambda x: x, url=req.url
    )


async def shorten_summary(
    req: ShortenPayload, request: Request, authorization: str = Header(None)
):
    token = open_ai_token_from_auth(authorization)
    async_generator = async_generator_summary_shorten(req.content, token)
    return stream(async_generator, req.use_sse, request, data_fn=lambda x: x)


import fastapi

app = fastapi.FastAPI()

app.post("/youtube_markdown")(youtube_summary_md)
app.post("/shorten_markdown")(shorten_summary)
app.post("/check")
