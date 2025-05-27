from typing import TypeVar, Generic, Type, Callable, Optional, Any
from sqlmodel import Session, select
from sqlmodel import SQLModel

T = TypeVar("T", bound=SQLModel)


class DeviceStateManager(Generic[T]):
    def __init__(
        self,
        model: Type[T],
        device_id: str,
        session: Session,
        on_state_update: Optional[Callable[[str, T], Any]] = None,
    ):
        self.model = model
        self.device_id = device_id
        self.session = session
        self._state: T | None = None
        self.on_state_update_func = on_state_update

    def load(self) -> T:
        # Lazy-load state from DB
        if self._state is None:
            statement = select(self.model).where(self.model.device_id == self.device_id)  # type: ignore
            result = self.session.exec(statement).first()
            if result is None:
                # create default state
                result = self.model(device_id=self.device_id)
                self.session.add(result)
                self.session.commit()
                self.session.refresh(result)
            self._state = result
        else:
            # this solves some wired issue where the state was not none but still not serialized properly
            self.session.refresh(
                self._state
            )  # ensure we have the latest state from the DB

        return self._state

    def save(self) -> None:
        if self._state:
            self.session.add(self._state)
            self.session.commit()
            self.session.refresh(self._state)

    def update(self, **kwargs) -> T:
        state = self.load()
        for key, value in kwargs.items():
            setattr(state, key, value)
        self.save()
        self._on_state_update(state)
        return state

    def get(self) -> T:
        return self.load()

    def reset(self) -> T:
        self._state = self.model(device_id=self.device_id)  # type: ignore
        self.save()
        self._on_state_update(self._state)
        return self._state

    def _on_state_update(self, state: T) -> None:
        if self.on_state_update_func:
            self.on_state_update_func(self.device_id, state)
