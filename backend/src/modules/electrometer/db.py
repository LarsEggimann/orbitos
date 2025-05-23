import os
from typing import Annotated
from sqlmodel import Session, SQLModel, create_engine
from fastapi import Depends

SQLITE_FILEPATH: str = os.path.join(os.path.dirname(__file__), "electrometer.db")
SQLITE_URL: str = f"sqlite:///{SQLITE_FILEPATH}"

connect_args = {"check_same_thread": False}
engine = create_engine(SQLITE_URL, connect_args=connect_args)


def _get_session():
    with Session(engine) as session:
        yield session


def init_db() -> None:
    SQLModel.metadata.create_all(engine)


SessionDep = Annotated[Session, Depends(_get_session)]
