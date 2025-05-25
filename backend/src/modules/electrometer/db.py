import os
from typing import Annotated
from sqlmodel import Session, SQLModel, create_engine
from fastapi import Depends

from src.modules.electrometer.models import ElectrometerState, CurrentData

SQLITE_FILEPATH: str = os.path.join(os.path.dirname(__file__), "electrometer.db")
SQLITE_URL: str = f"sqlite:///{SQLITE_FILEPATH}"

connect_args = {"check_same_thread": False}
engine = create_engine(SQLITE_URL, connect_args=connect_args)


def get_session():
    with Session(engine) as session:
        yield session

def init_db() -> None:
    tables = [SQLModel.metadata.tables[ElectrometerState.__tablename__], SQLModel.metadata.tables[CurrentData.__tablename__]]
    SQLModel.metadata.create_all(engine, tables=tables)

SessionDep = Annotated[Session, Depends(get_session)]
