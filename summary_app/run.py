from dataclasses import dataclass
from fastapi import FastAPI, Header
from fastapi.responses import StreamingResponse
from sse_starlette import EventSourceResponse


from api import get_async_generator_from_youtube

from loguru import logger


app = FastAPI()


@dataclass
class SummaryPayload:
    # could contain other things in the future
    # like whisper configs or openai configs
    url: str


def open_ai_token_from_auth(auth):
    if auth is None or not auth.startswith("Bearer "):
        return None
    _, token = auth.split(" ")
    return token


@app.post("/youtube")
async def youtube(
    req: SummaryPayload, authorization: str = Header(None)
) -> StreamingResponse:
    token = open_ai_token_from_auth(authorization)
    generator = await get_async_generator_from_youtube(req.url, token)
    logger.info(f"Streaming summary for {req.url}...")
    return StreamingResponse(generator, media_type="text/plain")


@app.post("/youtube_sse")
async def youtube_sse(
    req: SummaryPayload, authorization: str = Header(None)
) -> StreamingResponse:
    token = open_ai_token_from_auth(authorization)
    generator = await get_async_generator_from_youtube(req.url, token)

    async def event_stream():
        async for summary in generator:
            yield {"data": summary}
        yield {"data": "[DONE]"}

    logger.info(f"Streaming summary for {req.url}...")
    return EventSourceResponse(event_stream(), media_type="text/plain")
