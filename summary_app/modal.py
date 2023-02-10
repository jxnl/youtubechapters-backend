import asyncio
from dataclasses import dataclass
from fastapi import Header, Request
from fastapi.responses import StreamingResponse
from api import get_async_generator_from_youtube
from logging import getLogger
from sse_starlette import EventSourceResponse


import modal

from api import youtube_summary, stream_transcription

stub = modal.Stub("summary-v2")


def download_models():
    import whisper

    whisper.load_model("base")
    whisper.load_model("small")
    whisper.load_model("medium")


image = (
    modal.Image.debian_slim()
    .pip_install(
        [
            "youtube-transcript-api",
            "openai",
            "fastapi",
            "sse-starlette",
            "whisper",
            "loguru",
        ]
    )
    .run_function(download_models)
)


logger = getLogger(__name__)

stub.webhook(method="post")(youtube_summary)
stub.webhook(method="post")(stream_transcription)
