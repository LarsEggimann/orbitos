import os
from typing import Annotated
from sqlmodel import Session, SQLModel, create_engine
from fastapi import Depends

from src.core.db import get_session


SessionDep = Annotated[Session, Depends(get_session)]
