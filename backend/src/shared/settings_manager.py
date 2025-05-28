from typing import TypeVar, Generic, Type, Callable, Optional, Any
from sqlmodel import Session, select
from sqlmodel import SQLModel

T = TypeVar("T", bound=SQLModel)


class SettingsManager(Generic[T]):
    def __init__(
        self,
        model: Type[T],
        device_id: str,
        session: Session,
        on_settings_update: Optional[Callable[[str, T], Any]] = None,
    ):
        self.model = model
        self.device_id = device_id
        self.session = session
        self._settings: T | None = None
        self.on_settings_update_func = on_settings_update

    def load(self) -> T:
        # Lazy-load settings from DB
        if self._settings is None:
            statement = select(self.model).where(self.model.device_id == self.device_id)  # type: ignore
            result = self.session.exec(statement).first()
            if result is None:
                # create default settings
                result = self.model(device_id=self.device_id)
                self.session.add(result)
                self.session.commit()
                self.session.refresh(result)
            self._settings = result
        else:
            # this solves some wired issue where the settings was not none but still not serialized properly
            self.session.refresh(
                self._settings
            )  # ensure we have the latest settings from the DB

        return self._settings

    def save(self) -> None:
        if self._settings:
            self.session.add(self._settings)
            self.session.commit()
            self.session.refresh(self._settings)

    def update(self, **kwargs) -> T:
        settings = self.load()
        for key, value in kwargs.items():
            setattr(settings, key, value)
        self.save()
        self._on_settings_update(settings)
        return settings

    def get(self) -> T:
        return self.load()

    def reset(self) -> T:
        self._settings = self.model(device_id=self.device_id)  # type: ignore
        self.save()
        self._on_settings_update(self._settings)
        return self._settings
    
    def set_settings(self, settings: T) -> T:
        self._settings = settings
        self.save()
        self._on_settings_update(settings)
        return settings

    def _on_settings_update(self, settings: T) -> None:
        if self.on_settings_update_func:
            self.on_settings_update_func(self.device_id, settings)
