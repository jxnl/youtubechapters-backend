# Summary App

This fastapi application takes advantage of two things to be fast. It cannot summarize videos without transcripts.
It d

1. youtube videos may have transcripts that can be pulled via the transcript api, we do not take advantage of timestamps but we could.
2. we can use regular expressions as a tokenizer to approximatly fine setence boundaries, we could use something like spacy or nltk but it would just take longer

