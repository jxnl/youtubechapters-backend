from loguru import logger
from pytube import YouTube


def download_youtube_video(url):
    logger.info(f"Downloading {url}...")
    stream = YouTube(url).streams.filter(only_audio=True).first()

    if stream:
        logger.info("Downloading stream...")
        file_name = stream.download(output_path="./tmp")
        logger.info(f"Downloaded {url} to {file_name}")
        return file_name

    logger.info(f"Could not download {url}")
    return None


if __name__ == "__main__":
    filename = download_youtube_video("https://www.youtube.com/watch?v=9bZkp7q19f0")
    print(filename)
