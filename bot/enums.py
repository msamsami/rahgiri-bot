from enum import Enum


class Command(str, Enum):
    START = "start"
    TRACK = "track"
    TRACK_OUTPUT_TEXT = "text"
    TRACK_OUTPUT_IMAGE = "image"
    HELP = "help"
