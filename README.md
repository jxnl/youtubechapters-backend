# Youtube Summarizer 

This fastapi application takes advantage of two things to be fast. currently it cannot summarize youtube videos without transcripts. It also does not use the timestamps, which would be room for improvement.

## Why its 'fast' 
1. youtube videos may have transcripts that can be pulled via the transcript api, the transcript api along with whisper api will both contain phrases with {start_time, text} which could be used to improve summaries.
2. we can use regular expressions as a tokenizer to approximate sentence boundaries, we could use something like spacy or nltk but it would just take longer

### How whisper transcriptions could be faster

If we can figure out how to stream whisper transcriptions then we can start summarizing on the first `n_tokens` of whipser, making the time to first summarization token bounded to some extend by `time_to_download_video + time_to_produce_n_tokens`

## Running it yourself

```
pip install -r requirements.txt
# if you use poetry
# poetry init
```

## Running the Summary App

```
cd summary_app
uvicorn app:run:app --reload
```

## Calling the streaming endpoints

Usual streaming
```
curl --no-buffer -X 'POST' \
  'http://127.0.0.1:8000/youtube'\
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer <OPENAI_API_TOKEN>' \
  -d '{
  "url": "https://www.youtube.com/watch?v=9Q9_CQxFUKY"
}'
```

With SSE and `[DONE]` token, this is just made to look more like OPENAI's response.
```
curl --no-buffer -X 'POST' \
  'http://127.0.0.1:8000/youtube_sse'\
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer <OPENAI_API_TOKEN>' \
  -d '{
  "url": "https://www.youtube.com/watch?v=9Q9_CQxFUKY"
}'
```

## Future work

1. support whisper transcription
2. support streaming whisper transcription
3. design a way to use time stamps. (maybe yield `[t=12s]` token? )
  * in SSE we could return `{data: data, is_time: bool}`???