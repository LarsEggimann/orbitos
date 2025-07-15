from enum import Enum


class LinActStatus(str, Enum):
    EXTRACTED = "extracted"
    RETRACTED = "retracted"
    UNKNOWN = "unknown"

    def __str__(self) -> str:
        return str(self.value)
