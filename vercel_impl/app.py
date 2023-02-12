import api

from fastapi import FastAPI

app = FastAPI()


@app.get("/healthcheck")
def read_root():
    return {"status": "ok"}


app.post("/summarize_youtube")(api.youtube_summary)
app.post("/transcribe_youtube")(api.youtube_transcript)
