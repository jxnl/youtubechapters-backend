# Explanation of Youtube Summarization

# Description of the summary api

[video-summary-streamer/run.py at main · jxnl/video-summary-streamer](https://github.com/jxnl/video-summary-streamer/blob/main/timestamps_app/run.py#L26-L35)

```python
async def async_generator_summary_timestamps(
    url: str, use_whisper: bool = False, openai_api_key: Optional[str] = None
):
    video_id = extract_video_id(url)
    phrases = transcribe_youtube(video_id, use_whisper)
    phrases = group_speech_segments(phrases, max_length=300)
    phrases = summary_segments_to_md(
        phrases, openai_api_key=openai_api_key, video_id=video_id
    )
    return phrases

```

This API takes a YouTube URL, a "whisper" flag, and an optional OpenAI API key. It extracts the video ID, transcribes speech, batches phrases with start and end timestamps, and formats them into prompts. Batching bypasses the token limit, but comes with a cost.

## Step 1) Extract `videoID`

```python
def extract_video_id(url: str) -> str:
    match = re.search(
        r"^(?:https?:\/\/)?(?:www\.)?(?:youtu\.be\/|youtube\.com\/(?:embed\/|v\/|watch\?v=|watch\?.+&v=))((\w|-){11})(?:\S+)?$",
        url,
    )
    if match:
        return match.group(1)
    else:
        raise ValueError("Invalid youtube url")
```

Most videos are referenced by `videoID` which can be extracted using the provided regex. This regex supports both `youtube.com` and `youtu.be` which comes often as shortened urls. Its nice to support both since i know you intend on using nice routing tricks.

## Step 2) Transcription (whisper optional)

[video-summary-streamer/transcribe.py at main · jxnl/video-summary-streamer](https://github.com/jxnl/video-summary-streamer/blob/main/timestamps_app/transcribe.py)

For most modern videos, the transcript API takes the video ID (regex can be found in the `extract_video_id` function) and returns the whole transcript. It is also available as an npm package, [youtube-transcript](https://www.npmjs.com/package/youtube-transcript). It works as needed. I think supporting whisper should be left for later. If the transcript is missing, we can let the user know that whisper is a work-in-progress.

**Aside: Costs**

If you have the transcript, the cost of the summary will be.

```
# batch_size is set to ~ 9000
# max result tokens is about ~1000
transcript_tokens = len(transcripts) // 4
n_batchs = transcript_costs / batch_size
prompt_tokens = 400 * n_batchs
result_tokens = (max) max_tokens * n_batchs

tokens = transcript_costs + prompt_tokens + result_tokens
price_max = tokens * 0.02

```

If you make the default transcripts an async generator (or stream) It'll leave room to support whisper as a async generator (or stream) later on. Its helpful to have that `from_whisper boolean` attribute so we can change behavior later on in the code.

## Step 3) Mergeing phrases into larger phrase

[video-summary-streamer/segment.py at main · jxnl/video-summary-streamer](https://github.com/jxnl/video-summary-streamer/blob/main/timestamps_app/segment.py#L33-L66)

The function `group_speech_segments` takes the resulting transcript, and groups the segments into chunks of a maximum length (default: 300). It iterates over an AsyncGenerator of Segment objects (this generator is what allows to support whisper later), it merges adjacent segments that meet certain conditions. Specifically, if there is a pause of ~ seconds or more between them, or if the length of the combined segment exceeds the maximum length, the segment is yielded as a separate Segment object.

```
before: [
    {text:"this is"}, {text:"a phrase"}, {text:"or"}, {text:"another sentence"}, ...
    ]

after: [
    {text: "this is a prhase or another sentence"}, ...
]

```

There are a lot of parameters, but generally each transcript segment is very short. We want to merge them to identify where phrases start and end. This information can help us get more precise time stamps. It's best to stick to batches of 300 characters, and ignore other logic.

## Step 4) Batch requesting the summary in parts

[video-summary-streamer/segment.py at main · jxnl/video-summary-streamer](https://github.com/jxnl/video-summary-streamer/blob/main/timestamps_app/segment.py#L88-L120)

The `summary_segments_to_md` function receives the resulting segments and produces a summary of the transcript using the OpenAI API. It collects the batches and formats the prompt like this:

Each timestamped phrase is a "Segment" in this example. We accumulate them until we reach the batch size, then we make a request and start streaming out tokens.

```
<-- prompt instructions -->

Content:

timestamp: youtube.com/videoid?t=12s
this is a prhase or another sentence, this is a prhase or another sentence
this is a prhase or another sentence

timestamp: youtube.com/videoid?t=13s
this is a prhase or another sentence, this is a prhase or another sentence
this is a prhase or another sentence

<--- repeats until we hit token limit>

Notes:

```

The function initializes an empty string, `text`, and iterates through the input segments. For each segment, it checks if it was produced using whisper and, if so, sets a smaller chunk size for the summary request to improve performance.

It checks if `text` is less than the chunk size (9000 by default). If it is, it adds the current segment to `text`. Otherwise, it makes a summary request using the OpenAI API with `text` as the input, and yields the resulting tokens one by one using the `summarize_transcript` function. It then resets `text` to an empty string and increments a counter for the number of calls. Rate limiting can happen here to limit the maximum cost per video. Additionally, a button for 'Stop Generation' can be added to save compute. The function continues this process until all segments have been processed.

## Part 5) Summarization

Nothing special here, just the prompt: