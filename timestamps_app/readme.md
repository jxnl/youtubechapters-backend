# Description of the summary api

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

This is the basic entry point for the api, this function takes in a YouTube video URL, a boolean flag for using the "whisper" feature, and an optional OpenAI API key. It first extracts the video ID from the URL and then uses the transcribe_youtube function to transcribe the speech in the video.

## Step 1) Extract `videoID`

Most videos are referenced by `videoID` which can be extracted using the provided regex. This regex supports both `youtube.com` and `youtu.be` which comes often as shortened urls. Its nice to support both since i know you intend on using nice routing tricks.

## Step 2) Transcription (whisper optional)

For most modern videos the transcript api takes the videoId (regex can be found in the `extract_video_id` function) and returns the whole transcript, it also exists in npm as [youtube-transcript](https://www.npmjs.com/package/youtube-transcript) It works as needed. I think supporting whisper should be left til the later. If the transcript is missing we can let the user know that whisper is WIP.

**Aside: Costs**

If you have the transcript the cost of the summary will be.

```python
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


The resulting transcript is then passed to the `group_speech_segments` function, which groups the transcript into segments of a maximum length specified by the max_length parameter (300 by default). It does this by iterating over the input AsyncGenerator of Segment objects, and combining adjacent segments if they meet certain conditions. Specifically, if there is a pause of at least 0.01 seconds between two segments or if the length of the combined transcript exceeds max_length, the current segment is yielded as a separate Segment object.


```
before: [
    {text:"this is"}, {text:"a phrase"}, {text:"or"}, {text:"another sentence"}, ...
    ]

after: [
    {text: "this is a prhase or another sentence"}, ...
]

```

Theres are a lot of parameters here but generally each transcript segment is very short and we want to do some merging to know where 'phrases' really start and end. We can use this information to get better resolution of time stamps. It might be best just to keep it to batchs of 300 characters and ignore the other logic.

## Step 4) Batch requesting the summary in parts

The resulting segments are then passed to the `summary_segments_to_md` function, which produces a summary of the transcript using the OpenAI API.

It just collects the batchs together and formats the prompt do be something like what you see below:


Each timestamped phrase is a "Segment' in this example and we just accumilate them until we get to the batch size, the nwe can make a request and start streaming out tokens.

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

The function first initializes an empty string text, and then iterates over the input segments.

> **(aside for later**) For each segment, it checks if the segment was produced using whisper. If so, it sets a smaller chunk size for the summary request to improve performance (time to first summary token) it buys us a lot of rendering time.

It then checks if the accumilated text is less than the chunk size (9000 by default). If it is, it adds the current segment's text to text. Otherwise, it makes a summary request using the OpenAI API with text as the input, and yields the resulting tokens one by one using the `summarize_transcript` function. It then resets text to an empty string and increments a counter `n_calls` **Rate limiting can happen here to limit the max cost per video since i bet people will try it on 2hr long podcasts**. The function continues this process until all segments have been processed. **Its also good to have a button for 'stop generation' to save us some compute.**