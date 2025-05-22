from typing import TypeVar, Generic, Type
from sqlmodel import Session, select
from sqlmodel import SQLModel

T = TypeVar("T", bound=SQLModel)

class DeviceStateManager(Generic[T]):
    def __init__(self, model: Type[T], device_id: str, session: Session):
        self.model = model
        self.device_id = device_id
        self.session = session
        self._state: T | None = None

    def load(self) -> T:
        # Lazy-load state from DB
        if self._state is None:
            statement = select(self.model).where(self.model.id == self.device_id) # type: ignore
            result = self.session.exec(statement).first()
            if result is None:
                # create default state
                result = self.model(id=self.device_id)
                self.session.add(result)
                self.session.commit()
                self.session.refresh(result)
            self._state = result
        return self._state

    def save(self) -> None:
        if self._state:
            self.session.add(self._state)
            self.session.commit()

    def update(self, **kwargs) -> T:
        state = self.load()
        for key, value in kwargs.items():
            setattr(state, key, value)
        self.save()
        return state

    def get(self) -> T:
        return self.load()

    def reset(self) -> T:
        self._state = self.model(id=self.device_id)
        self.save()
        return self._state
