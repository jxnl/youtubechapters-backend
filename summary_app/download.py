from pytube import YouTube
from tempfile import TemporaryDirectory
from loguru import logger


def download_youtube_video(url):
    logger.info(f"Downloading {url}...")
    with TemporaryDirectory() as tmpdir:
        file_name = (
            YouTube(url)
            .streams.filter(only_audio=True, file_extension="mp4")
            .first()
            .download(output_path="./tmp")
        )
        logger.info(f"Downloaded {url} to {file_name}")
        return file_name
