from fastapi import FastAPI
from api import youtube_summary, stream_transcription

app = FastAPI()


@app.get("/healthcheck")
def read_root():
    return {"status": "ok"}


# we do this so that we can use the same endpoint for both
# the modal and the web app
app.post("/summarize_youtube")(youtube_summary)
app.post("/stream_transcription")(stream_transcription)
