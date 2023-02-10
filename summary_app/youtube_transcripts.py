import re
import requests
from typing import AsyncGenerator
from youtube_transcript_api import YouTubeTranscriptApi
from dataclasses import dataclass
from loguru import logger

from download import download_youtube_video
from phrase_block import PhraseBlock
from transcribe import whisper_generator


def extract_video_id(url):
    match = re.search(
        r"^(?:https?:\/\/)?(?:www\.)?(?:youtu\.be\/|youtube\.com\/(?:embed\/|v\/|watch\?v=|watch\?.+&v=))((\w|-){11})(?:\S+)?$",
        url,
    )
    if match:
        return match.group(1)
    return None


def create_youtube_url(video_id):
    return f"https://www.youtube.com/watch?v={video_id}"


async def transcribe_youtube(
    video_id: str, local=False
) -> AsyncGenerator[PhraseBlock, None]:
    # this function will try to get the transcript from youtube
    try:
        transcript = YouTubeTranscriptApi.get_transcript(video_id)
        logger.info("transcript found on youtube no need to download video")
        for t in transcript:
            yield PhraseBlock(start=t["start"], text=t["text"])
    except Exception:
        logger.info(
            f"usually this means that the video has transcripts disabled, we will have to use whisper instead"
        )
        if local:
            logger.info(
                "downloading video locally... and transcribing with local model"
            )
            url = create_youtube_url(video_id)
            path = download_youtube_video(url)
            async for block in whisper_generator(path, model="tiny"):
                yield PhraseBlock(block["start"], block["text"])

        else:
            logger.info("transcribing with whisper on remote gpu...")
            async for block in _transcribe_youtube_whisper(video_id):
                yield block


async def _transcribe_youtube_whisper(video_id) -> AsyncGenerator[PhraseBlock, None]:
    # this function will try to get the transcript from whisper on a remote gpu
    url = "https://jxnl--youtube-stream-transcription.modal.run"

    youtube = create_youtube_url(video_id)
    data = {"url": youtube, "use_sse": False, "model": "base"}

    r = requests.post(url, json=data, stream=True)
    r.raise_for_status()

    for chunk in r.iter_content():
        # chunk is a byte string.
        str_chunk = chunk.decode("utf-8")
        yield PhraseBlock(start=None, text=str_chunk)
