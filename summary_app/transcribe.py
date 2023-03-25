import json
import os
from typing import AsyncGenerator

import requests
from loguru import logger
from segment import Segment
from youtube_transcript_api import YouTubeTranscriptApi

TRAN_URL = os.environ.get("TRAN_URL")


def create_youtube_url(video_id):
    return f"https://www.youtube.com/watch?v={video_id}"


async def transcribe_youtube(
    video_id: str, use_whisper=False, model: str = "base"
) -> AsyncGenerator[Segment, None]:
    if use_whisper:
        logger.info(f"Forcing whisper: calling out to remote gpu for {video_id}")
        async for block in _transcribe_youtube_whisper(video_id, model):
            yield block
    else:
        # this function will try to get the transcript from youtube
        try:
            transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)

            # Get either 'en' or the first generated transcript
            language_code = None
            for t in transcript_list:
                if t.is_generated:
                    language_code = t.language_code
                    break

            logger.info(f"Transcript {video_id} language code: {language_code}")

            transcript = YouTubeTranscriptApi.get_transcript(
                video_id, ("en", language_code)
            )
            logger.info("Transcript found on youtube no need to download video")
            for t in transcript:
                yield Segment(
                    language=language_code or "en",
                    start_time=t["start"],
                    end_time=t["start"] + t["duration"],
                    transcript=t["text"],
                )
        except Exception as e:
            logger.info(
                f"Video has transcripts disabled, using whisper to transcribe {e}"
            )
            logger.info(f"Fallback whisper: calling out to remote gpu for {video_id}")
            async for block in _transcribe_youtube_whisper(video_id, model):
                yield block


async def _transcribe_youtube_whisper(video_id, model) -> AsyncGenerator[Segment, None]:
    # this function will try to get the transcript from whisper on a remote gpu
    url = TRAN_URL

    youtube = create_youtube_url(video_id)
    data = {"url": youtube, "use_sse": True, "model": model}

    r = requests.post(url, json=data, stream=True)
    r.raise_for_status()

    for chunk in r.iter_content(chunk_size=40000):
        try:
            data = chunk.decode("utf-8").split(":", 1)[1]
            if data.strip() == "[DONE]":
                logger.info("Done with transcription")
            else:
                data = json.loads(data)
                yield Segment(
                    start_time=data["start"],
                    end_time=data["end"],
                    transcript=data["text"],
                    from_whisper=True,
                )
        except Exception as e:
            logger.info(f"Error decoding chunk {e}")
            pass
