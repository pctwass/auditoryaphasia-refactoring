from enum import Enum

class AudioStatus(Enum):
    INITIAL : 0
    PLAYING: 1
    FINISHED_PLAYING : 2
    TERMINATED : 3


class TrialClassificationStatus(Enum):
    UNDECODED : 0
    DECODED : 1
    DECODED_EARLY : 2