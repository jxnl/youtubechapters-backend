import modal

from api import youtube_summary, stream_transcription


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
stub.webhook(method="POST")(youtube_summary)
stub.webhook(method="POST", gpu="any")(stream_transcription)
