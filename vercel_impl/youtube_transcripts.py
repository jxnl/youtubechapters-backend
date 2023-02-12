import re
import requests
from typing import AsyncGenerator

from youtube_transcript_api import YouTubeTranscriptApi
from loguru import logger

from phrase_block import PhraseBlock


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


async def transcribe_youtube(video_id: str) -> AsyncGenerator[PhraseBlock, None]:
    transcript = YouTubeTranscriptApi.get_transcript(video_id)
    logger.info("transcript found on youtube no need to download video")
    for t in transcript:
        print(t)
        yield PhraseBlock(
            start=t["start"], text=t["text"], end=t["start"] + t["duration"]
        )
