from datetime import datetime
from typing import Annotated, Optional
from fastapi import Depends

from src.shared.models import TimeFrameInput


async def time_frame_input(
    start: Optional[datetime] = None, end: Optional[datetime] = None
) -> TimeFrameInput:
    return TimeFrameInput(
        start=start,
        end=end,
    )


TimeFrameInputDep = Annotated[TimeFrameInput, Depends(time_frame_input)]
