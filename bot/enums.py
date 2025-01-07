from enum import Enum


class Command(str, Enum):
    START = "start"
    TRACK = "track"
    HELP = "help"
