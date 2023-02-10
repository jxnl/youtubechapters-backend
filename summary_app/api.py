from loguru import logger
from batch_summarize import generate_batchs, stream_summaries_from_text
from youtube import extract_video_id, transcribe_youtube


async def get_async_generator_from_youtube(url: str, openai_api_key: str = None):
    """
    This function is used to get a generator from a youtube url
    """
    logger.info(f"Received request for {url}")
    video_id = extract_video_id(url)
    logger.info(f"Extracted video id {video_id}")

    try:
        # if we can't get the transcript, we can't summarize it
        # so we raise an error, eventually this will be handled
        # by requesting a transcription by whisper
        blocks = transcribe_youtube(video_id)
    except Exception as e:
        logger.exception(e)
        raise ValueError("Video transcript not found on youtube")

    batchs = generate_batchs(blocks)
    generator = stream_summaries_from_text(batchs, openai_api_key)
    return generator
