import asyncio
import json
from dataclasses import dataclass

import modal
from download import download_youtube_video
from fastapi import Request
from fastapi.responses import StreamingResponse
from loguru import logger
from modal import web_endpoint
from sse_starlette import EventSourceResponse
from transcribe import transcribe


def download_models():
    import whisper

    whisper.load_model("tiny")
    whisper.load_model("base")
    whisper.load_model("small")
    whisper.load_model("medium")


image = (
    modal.Image.debian_slim()
    .apt_install("ffmpeg")
    .pip_install(
        [
            "youtube-transcript-api",
            "openai",
            "fastapi",
            "sse-starlette",
            "openai-whisper",
            "loguru",
            "ffmpeg-python",
            "watchfiles",
            "pytube",
        ]
    )
    .run_function(download_models)
)

stub = modal.Stub("youtube", image=image)


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
class TranscriptionPayload:
    url: str
    use_sse: bool = False
    model: str = "tiny"


@stub.function(gpu="A100")
@web_endpoint(method="POST")
async def stream_transcription_v2(req: TranscriptionPayload, request: Request):
    import whisper

    model = whisper.load_model(req.model)
    path = download_youtube_video(req.url)
    generator = transcribe(model, path)
    return stream(generator, req.use_sse, request, data_fn=lambda x: x["text"])


@stub.function(gpu="A100")
@web_endpoint(method="POST")
async def stream_transcription_segment_v2(req: TranscriptionPayload, request: Request):
    import whisper

    model = whisper.load_model(req.model)
    path = download_youtube_video(req.url)
    generator = transcribe(model, path)
    return stream(
        generator,
        req.use_sse,
        request,
        data_fn=lambda x: json.dumps(
            dict(
                start=x["start"],
                text=x["text"],
                end=x["end"],
            )
        ),
    )
