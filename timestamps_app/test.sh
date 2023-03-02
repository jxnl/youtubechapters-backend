curl --no-buffer -X 'POST' \
   'http://127.0.0.1:3000/youtube_markdown'\
   -H 'accept: application/json' \
   -H 'Content-Type: application/json' \
   -H 'Authorization: Bearer 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' \
   -d '{
   "use_whisper": false,
   "url": "https://www.youtube.com/watch?v=9w0DbbmMJBU",
   "use_cache": false
 }'

curl --no-buffer -X 'POST' \
  'https://youtube-markdown.fly.dev/youtube_markdown'\
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer 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' \
  -d '{
  "url": "https://www.youtube.com/watch?v=9Q9_CQxFUKY",
  "use_sse": true 
}'

curl --no-buffer -X 'POST' \
  'https://jxnl--youtube-stream-transcription-segment-dev.modal.run'\
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer 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' \
  -d '{
  "use_sse": true,
  "url": "https://www.youtube.com/watch?v=9Q9_CQxFUKY"
}'