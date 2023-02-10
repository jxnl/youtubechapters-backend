import modal

from api import TranscriptionPayload, stream
from download import download_youtube_video
from fastapi import Request
from transcribe import transcribe
import whisper


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

model = whisper.load_model("base")


@stub.webhook(method="POST", gpu="any")
async def stream_transcription(req: TranscriptionPayload, request: Request):
    path = download_youtube_video(req.url)
    generator = transcribe(model, path)
    return stream(generator, req.use_sse, request, data_fn=lambda x: x["text"])
