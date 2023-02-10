import re
from youtube_transcript_api import YouTubeTranscriptApi
from dataclasses import dataclass

video_id = "O_9JoimRj8w"


@dataclass
class PhraseBlock:
    # this is only to be more self documenting
    # in case we want to support whisper
    start: float
    text: str


def extract_video_id(url):
    match = re.search(
        r"^(?:https?:\/\/)?(?:www\.)?(?:youtu\.be\/|youtube\.com\/(?:embed\/|v\/|watch\?v=|watch\?.+&v=))((\w|-){11})(?:\S+)?$",
        url,
    )
    if match:
        return match.group(1)
    return None


async def transcribe_youtube(video_id: str):
    """
    Given a youtube video id, return the transcript as a list of phrases that contain start times and text
    """
    try:
        # we do this yield just cause i want to build in streaming
        # support for whisper in the future
        transcript = YouTubeTranscriptApi.get_transcript(video_id)
        for t in transcript:
            yield PhraseBlock(start=t["start"], text=t["text"])
    except Exception as e:
        # usually this means that there is no transcript
        # or that the video is private, etc.
        # in the future i'd like to make a request to make a whiper api call
        raise Exception(
            f"Could not get transcript for {video_id} most likely there was no transcript available."
        ) from e
