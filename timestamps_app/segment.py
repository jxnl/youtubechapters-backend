from dataclasses import dataclass, field
from datetime import timedelta
from typing import AsyncGenerator
from loguru import logger
from md_summarize import summarize_transcript


@dataclass
class Segment:
    start_time: float
    end_time: float
    transcript: str = field(repr=False)
    transcript_length: int = field(init=False, default=0)
    timestamp: str = field(init=False, repr=True)
    from_whisper: bool = field(default=False)

    def __post_init__(self):
        self.transcript_length = len(self.transcript)
        self.start_time = round(self.start_time)
        self.timestamp = str(timedelta(seconds=self.start_time))

    def to_str(self, video_id):
        return "timestamp:{ts} url:{url}\ntranscript:\n{transcript}".format(
            ts=self.timestamp,
            s=self.start_time,
            url=f"https://youtu.be/{video_id}?t={self.start_time}s",
            transcript=self.transcript,
        )


async def group_speech_segments(
    segments: AsyncGenerator[Segment, None], max_length=300
):
    current_segment = await segments.__anext__()
    current_transcript = current_segment.transcript
    current_start_time = current_segment.start_time
    from_whisper = current_segment.from_whisper

    async for segment in segments:
        previous_segment = current_segment
        current_segment = segment

        is_pause = (current_segment.start_time - previous_segment.end_time) > 0.01
        is_long = current_segment.start_time - current_start_time > 1
        is_too_long = len(current_transcript) > max_length

        if (is_long and is_pause) or is_too_long:
            yield Segment(
                start_time=current_start_time,
                end_time=previous_segment.end_time,
                transcript=current_transcript.strip(),
                from_whisper=from_whisper,
            )
            current_transcript = ""
            current_start_time = current_segment.start_time
        else:
            current_transcript += " " + current_segment.transcript

    yield Segment(
        start_time=current_start_time,
        end_time=current_segment.end_time,
        transcript=current_transcript.strip(),
        from_whisper=from_whisper,
    )


async def summary_segments_to_md(
    segments, video_id=None, openai_api_key=None, chunk=5000
):
    text = ""
    n_calls = 0
    async for block in segments:
        if block.from_whisper:
            # instead of using the chunk size, this gets us
            # faster results by using a smaller chunk size
            chunk = [500, 1000, 3000, 4000][n_calls if n_calls < 4 else -1]
            logger.info(f"Setting chunk size to {chunk} for {video_id}")

        if len(text) < chunk:
            text += f"\n\n{block.to_str(video_id)}"
        else:
            n_calls += 1
            logger.info(
                f"Making summary request for {video_id}, requet_size: {len(text)}, n_calls: {n_calls}"
            )
            async for token in await summarize_transcript(
                text, openai_api_key=openai_api_key
            ):
                yield token
            text = ""
            logger.info(f"Finished n={n_calls} summary request for {video_id}")
    if text != "":
        n_calls += 1
        logger.info(f"Making summary request for {video_id}, n_calls: {n_calls}")
        async for token in await summarize_transcript(
            text, openai_api_key=openai_api_key
        ):
            yield token
    logger.info(f"Finished summary request for {video_id} in {n_calls} calls")
