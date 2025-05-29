import copy
from typing import TypeVar, Generic, Type, Callable, Optional, Any
from sqlmodel import select, Session
from sqlalchemy.engine import Engine

from src.shared.models import BaseSetting

T = TypeVar("T", bound=BaseSetting)

class SettingsManager(Generic[T]):
    def __init__(
        self,
        model: Type[T],
        device_id: str,
        engine: Engine,
        on_settings_update: Optional[Callable[[str, T], Any]] = None,
    ):
        self.model = model
        self.device_id = device_id
        self.engine = engine
        self._settings: T | None = None
        self.on_settings_update_func = on_settings_update
        self._settings_before_change: T | None = None

    def load(self) -> T:
        # Always load from DB and update _settings
        with Session(self.engine) as session:
            statement = select(self.model).where(self.model.device_id == self.device_id)  # type: ignore
            result = session.exec(statement).first()
            if result is None:
                result = self.model(device_id=self.device_id)
                session.add(result)
                session.commit()
                session.refresh(result)

            self._settings = result.model_copy(deep=True) # Detach from session

        return self._settings

    def save(self) -> None:
        if self._settings:
            with Session(self.engine) as session:
                db_obj = session.get(self.model, self.device_id)

                if db_obj:

                    update_data = self._settings.model_dump(exclude_unset=False) # Get all fields

                    for key, value in update_data.items():
                        if hasattr(db_obj, key): # ensure attribute exists on the model
                            setattr(db_obj, key, value)

                    session.add(db_obj)
                else:
                    new_obj_data = self._settings.model_dump()
                    db_obj = self.model.model_validate(new_obj_data)
                    session.add(db_obj)
                
                session.commit()
                session.refresh(db_obj) # refresh to get any DB-side changes
                self._settings = db_obj.model_copy(deep=True) # store a detached copy

    def update(self, **kwargs) -> T:
        current_settings_state = self.get()
        
        self._settings_before_change = current_settings_state.model_copy(deep=True)

        updated_data = current_settings_state.model_dump()

        for key, value in kwargs.items():
            if key in self.model.model_fields:
                updated_data[key] = value

        self._settings = self.model.model_validate(updated_data)

        self.save() # persist the new state of self._settings
        
        self._on_settings_update(self._settings)
        
        return self._settings

    def undo_last_update(self) -> T:
        if not self._settings_before_change:
            raise ValueError("No previous settings to revert to.")
        
        self._settings = self._settings_before_change.model_copy(deep=True) # use a fresh copy
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

    def _on_settings_update(self, settings: T) -> None:
        if self.on_settings_update_func:
            self.on_settings_update_func(self.device_id, settings)