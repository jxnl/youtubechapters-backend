import whisper
from pytube import YouTube
from tempfile import TemporaryDirectory, TemporaryFile
from loguru import logger


def download_youtube_video(url):
    with TemporaryDirectory() as tmpdir:
        file_name = (
            YouTube(url)
            .streams.filter(only_audio=True, file_extension="mp4")
            .first()
            .download(output_path="./")
        )
        logger.info(f"Downloaded {url} to {file_name}")
        return file_name


model = whisper.load_model("small")


async def transcribe_youtube(path):
    resp = model.transcribe(path, verbose=True)
    return resp["text"]


path = download_youtube_video("https://www.youtube.com/watch?v=FECyn_sGk4M")
print(transcribe_youtube(path))
