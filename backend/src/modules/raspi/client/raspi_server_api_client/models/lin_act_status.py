from enum import Enum


class LinActStatus(str, Enum):
    EXTENDED = "extended"
    RETRACTED = "retracted"
    UNKNOWN = "unknown"

    def __str__(self) -> str:
        return str(self.value)
