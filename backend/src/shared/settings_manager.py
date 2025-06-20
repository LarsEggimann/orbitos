from typing import TypeVar, Generic, Type, Callable, Optional, Any
from sqlmodel import Session
from sqlalchemy.engine import Engine

from src.shared.models import BaseSetting

T = TypeVar("T", bound=BaseSetting)


class SettingsManager(Generic[T]):
    def __init__(
        self,
        model: Type[T],
        device_id: int,
        device_name: str,
        engine: Engine,
        on_settings_update: Optional[Callable[[str, T], Any]] = None,
    ):
        self.model = model
        self.device_id = device_id
        self.device_name = device_name
        self.engine = engine
        self._settings: T | None = None
        self.on_settings_update_func = on_settings_update
        self._settings_before_change: T | None = None

    def load(self) -> T:
        # Always load from DB and update _settings
        with Session(self.engine) as session:
            result = session.get(self.model, self.device_id)
            if result is None:
                result = self.model(device_id=self.device_id)
                session.add(result)
                session.commit()
                session.refresh(result)

            self._settings = result.model_copy(deep=True)  # Detach from session

        return self._settings

    def save(self) -> None:
        if self._settings:
            with Session(self.engine) as session:
                merged_obj = session.merge(self._settings)
                session.commit()
                session.refresh(merged_obj)
                self._settings = merged_obj.model_copy(deep=True)

    def update(self, **kwargs) -> T:
        current_settings_state = self.get()

        self._settings_before_change = current_settings_state.model_copy(deep=True)

        updated_data = current_settings_state.model_dump()

        for key, value in kwargs.items():
            if key in self.model.model_fields:
                updated_data[key] = value

        self._settings = self.model.model_validate(updated_data)

        self.save()  # persist the new state of self._settings

        self._on_settings_update(self._settings)

        return self._settings

    def undo_last_update(self) -> T:
        if not self._settings_before_change:
            raise ValueError("No previous settings to revert to.")

        self._settings = self._settings_before_change.model_copy(
            deep=True
        )  # use a fresh copy
        self.save()
        self._on_settings_update(self._settings)
        return self._settings

    def get(self) -> T:
        if self._settings is None:
            return self.load()
        return self._settings

    def reset(self) -> T:
        self._settings = self.model(device_id=self.device_id)  # type: ignore
        self.save()
        self._on_settings_update(self._settings)
        return self._settings

    def set_settings(self, settings: T) -> T:
        self._settings = settings.model_copy(deep=True)
        self.save()
        self._on_settings_update(self._settings)
        return self._settings

    def get_changed_fields_compared_to_settings_before_change(self) -> dict[str, Any]:
        if not self._settings_before_change:
            raise ValueError("No previous settings to compare against.")

        current_settings = self.get()
        changed_fields = {}

        for field in current_settings.model_fields:
            current_value = getattr(current_settings, field)
            previous_value = getattr(self._settings_before_change, field)
            if current_value != previous_value:
                changed_fields[field] = (previous_value, current_value)

        return changed_fields

    def _on_settings_update(self, settings: T) -> None:
        if self.on_settings_update_func:
            self.on_settings_update_func(self.device_name, settings)
