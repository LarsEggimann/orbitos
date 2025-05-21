from sqlmodel import Session
from sqlalchemy.engine import Engine

class PersistentSessionManager:
    def __init__(self, engine: Engine):
        self.engine = engine
        self._session: Session | None = None

    def init_session(self) -> None:
        if self._session is None:
            self._session = Session(self.engine)

    def get_session(self) -> Session:
        if self._session is None:
            raise RuntimeError("Session not initialized. Call init_session() first.")
        return self._session

    def close_session(self) -> None:
        if self._session is not None:
            self._session.close()
            self._session = None
