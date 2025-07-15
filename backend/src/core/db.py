from typing import Annotated
from sqlmodel import Session, SQLModel, create_engine
from fastapi import Depends

from src.core.config import config

from src.modules.chopperwheel.models import CWSettings, CWData
from src.modules.xy_stages.models import XYStagesSettings, XYStagesData
from src.modules.raspi.models import RaspiSettings, RaspiData


connect_args = {"check_same_thread": False}
engine = create_engine(config.SQLITE_URL, connect_args=connect_args)


def get_session():
    with Session(engine) as session:
        yield session

SessionDep = Annotated[Session, Depends(get_session)]

def init_db() -> None:
    print("Initializing database...")
    tables = [
        SQLModel.metadata.tables[CWSettings.__tablename__],
        SQLModel.metadata.tables[CWData.__tablename__],
        SQLModel.metadata.tables[XYStagesSettings.__tablename__],
        SQLModel.metadata.tables[XYStagesData.__tablename__],
        SQLModel.metadata.tables[RaspiSettings.__tablename__],
        SQLModel.metadata.tables[RaspiData.__tablename__],

    ]
    SQLModel.metadata.create_all(engine, tables=tables)
