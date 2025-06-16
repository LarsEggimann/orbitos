from typing import TypeVar, Generic, Type, Callable, Optional, Any

from src.shared.models import BaseState

T = TypeVar("T", bound=BaseState)


class StateManager(Generic[T]):
    def __init__(
        self,
        model: Type[T],
        device_name: str,
        on_state_update: Optional[Callable[[str, T], Any]] = None,
    ):
        self.model = model
        self.device_name = device_name
        self._state: T | None = self.model(device_name=device_name)  # type: ignore
        self.on_state_update_func = on_state_update

    def load(self) -> T:
        if self._state is None:
            self._state = self.model(device_name=self.device_name)  # type: ignore
        return self._state

    def update(self, **kwargs) -> T:
        state = self.load()
        for key, value in kwargs.items():
            setattr(state, key, value)
        self._on_state_update(state)
        return state

    def get(self) -> T:
        return self.load()

    def _on_state_update(self, state: T) -> None:
        if self.on_state_update_func:
            self.on_state_update_func(self.device_name, state)
