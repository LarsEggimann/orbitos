from sqlmodel import Session, SQLModel, create_engine

from src.core.config import config

from src.modules.chopperwheel.models import CWSettings, CWData


connect_args = {"check_same_thread": False}
engine = create_engine(config.SQLITE_URL, connect_args=connect_args)


def get_session():
    with Session(engine) as session:
        yield session


def init_db() -> None:
    print("Initializing database...")
    tables = [
        SQLModel.metadata.tables[CWSettings.__tablename__],
        SQLModel.metadata.tables[CWData.__tablename__],
    ]
    SQLModel.metadata.create_all(engine, tables=tables)
