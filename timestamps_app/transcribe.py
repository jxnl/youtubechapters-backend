import json
import requests

from loguru import logger
from typing import AsyncGenerator
from youtube_transcript_api import YouTubeTranscriptApi

from segment import Segment


def create_youtube_url(video_id):
    return f"https://www.youtube.com/watch?v={video_id}"


async def transcribe_youtube(
    video_id: str, use_whisper=False, model: str = "tiny"
) -> AsyncGenerator[Segment, None]:
    if use_whisper:
        logger.info("Calling out to remote gpu")
        async for block in _transcribe_youtube_whisper(video_id, model):
            yield block
    else:
        # this function will try to get the transcript from youtube
        try:
            transcript = YouTubeTranscriptApi.get_transcript(video_id)
            logger.info("transcript found on youtube no need to download video")
            for t in transcript:
                yield Segment(
                    start_time=t["start"],
                    end_time=t["start"] + t["duration"],
                    transcript=t["text"],
                )
        except Exception as e:
            logger.info(
                f"Video has transcripts disabled, using whisper to transcribe {e}"
            )
            logger.info("Calling out to remote gpu")
            async for block in _transcribe_youtube_whisper(video_id, model):
                yield block


async def _transcribe_youtube_whisper(video_id, model) -> AsyncGenerator[Segment, None]:
    # this function will try to get the transcript from whisper on a remote gpu
    url = "https://jxnl--youtube-stream-transcription-segment.modal.run"

    youtube = create_youtube_url(video_id)
    data = {"url": youtube, "use_sse": True, "model": model}

    r = requests.post(url, json=data, stream=True)
    r.raise_for_status()

    for chunk in r.iter_content(chunk_size=40000):
        try:
            data = json.loads(chunk.decode("utf-8").split(":", 1)[1])
            yield Segment(
                start_time=data["start"],
                end_time=data["end"],
                transcript=data["text"],
                from_whisper=True,
            )
        except Exception as e:
            # this is a hack to handle the case where the last chunk is not a full chunk
            logger.info(f"Error decoding chunk {e}")
            pass
