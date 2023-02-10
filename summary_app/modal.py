import modal

from api import youtube_summary, stream_transcription


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

stub = modal.Stub("summary-v2", image=image)
stub.webhook(method="post")(youtube_summary)
stub.webhook(method="post")(stream_transcription)
