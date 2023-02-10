import asyncio
from dataclasses import dataclass
from fastapi import Header, Request
from fastapi.responses import StreamingResponse
from sse_starlette import EventSourceResponse


from loguru import logger


from batch_summarize import generate_batchs, stream_summaries_from_text
from youtube import extract_video_id, transcribe_youtube
from download import download_youtube_video
from transcribe import transcribe_generator


def get_async_generator_from_youtube(url: str, openai_api_key: str = None):
    # this is a helper function to get a generator that yields summaries
    logger.info(f"Received request for {url}")
    video_id = extract_video_id(url)
    logger.info(f"Extracted video id {video_id}")

    try:
        # if we can't get the transcript, we can't summarize it
        # so we raise an error, eventually this will be handled
        # by requesting a transcription by whisper
        blocks = transcribe_youtube(video_id)
    except Exception as e:
        logger.exception(e)
        raise ValueError("Video transcript not found on youtube")

    batchs = generate_batchs(blocks)
    generator = stream_summaries_from_text(batchs, openai_api_key)
    return generator


def get_generator_transcribe_youtube(url, model):
    # this is a helper function to get a generator that yields transcripts
    path = download_youtube_video(url)
    generator = transcribe_generator(path, model)
    logger.info(f"Transcribing {url} queue returned...")
    return generator


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
                    yield {"data": data} if use_sse else data
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
class BasePayload:
    # could contain other things in the future
    # like whisper configs or openai configs
    url: str
    use_sse: bool = False


@dataclass
class TranscriptionPayload(BasePayload):
    model: str = "tiny"


async def stream_transcription(req: TranscriptionPayload, request: Request):
    generator = get_generator_transcribe_youtube(req.url, model=req.model)
    return stream(generator, req.use_sse, request, data_fn=lambda x: x["text"])


async def youtube_summary(
    req: BasePayload, request: Request, authorization: str = Header(None)
):
    token = open_ai_token_from_auth(authorization)
    async_generator = get_async_generator_from_youtube(req.url, token)
    return stream(async_generator, req.use_sse, request)
