import asyncio
from dataclasses import dataclass
from fastapi import Header, Request
from fastapi.responses import StreamingResponse
from sse_starlette import EventSourceResponse

from loguru import logger

from summarize import merge_phrases, stream_summaries_from_text
from youtube_transcripts import extract_video_id, transcribe_youtube


def async_generator_summary(url: str, openai_api_key: str = None):
    # this is a helper function to get a generator that yields summaries
    # would be nice to have a functional way to do this
    #   url.apply(extract_video_id)
    #      .apply(transcribe_youtube)
    #      .batch(merge_phrases) (acc := "", if acc > batch_size; yield acc; else  acc+= x; acc = [])
    #      .map(stream_summaries_from_text)
    #      .tostream(
    #           use_sse=True,
    #           cancel_on_disconnect=request.is_disconnected
    #      )
    logger.info(f"Received request for {url}")
    video_id = extract_video_id(url)
    phrases = transcribe_youtube(video_id)
    phrases = merge_phrases(phrases)
    phrases = stream_summaries_from_text(phrases, openai_api_key)
    return phrases


def async_generator_transcript(url: str):
    logger.info(f"Received request for {url}")
    video_id = extract_video_id(url)
    phrases = transcribe_youtube(video_id)
    return phrases


def open_ai_token_from_auth(auth):
    if auth is None or not auth.startswith("Bearer "):
        return None
    _, token = auth.split(" ")
    return token


def stream(generator, use_sse: bool, request: Request, data_fn=lambda x: x):
    # this is a helper function to stream data from a generator in a fastapi endpoint
    # It handles both SSE and regular streaming responses and disconnects
    async def stream_obj():
        try:
            async for obj in generator:
                if obj and not await request.is_disconnected():
                    data = data_fn(obj)
                    yield {"data": str(data)} if use_sse else str(data)
            if use_sse:
                yield {"data": "[DONE]"}
        except asyncio.CancelledError as e:
            logger.info(f"Streaming canceled.")
            raise e

    response = EventSourceResponse if use_sse else StreamingResponse
    return response(
        stream_obj(),
        media_type="text/plain",
    )


@dataclass
class SummaryPayload:
    url: str
    use_sse: bool = False


async def youtube_summary(
    req: SummaryPayload, request: Request, authorization: str = Header(None)
):
    token = open_ai_token_from_auth(authorization)
    async_generator = async_generator_summary(req.url, token)
    return stream(async_generator, req.use_sse, request, data_fn=lambda x: x.text)


async def youtube_transcript(req: SummaryPayload, request: Request):
    async_generator = async_generator_transcript(req.url)
    return stream(async_generator, req.use_sse, request, data_fn=lambda x: x.text)
