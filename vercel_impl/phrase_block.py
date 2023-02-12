from dataclasses import dataclass


@dataclass
class PhraseBlock:
    # this is only to be more self documenting
    # in case we want to support whisper
    start: float
    end: float
    text: str
