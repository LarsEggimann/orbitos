from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.pandora_state_relays import PandoraStateRelays
    from ..models.pandora_state_wheels import PandoraStateWheels
    from ..models.temperature_sensor_state import TemperatureSensorState


T = TypeVar("T", bound="PandoraState")


@_attrs_define
class PandoraState:
    """
    Attributes:
        wheels (PandoraStateWheels | Unset):
        relays (PandoraStateRelays | Unset):
        temperature_sensor (TemperatureSensorState | Unset):
    """

    wheels: PandoraStateWheels | Unset = UNSET
    relays: PandoraStateRelays | Unset = UNSET
    temperature_sensor: TemperatureSensorState | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        wheels: dict[str, Any] | Unset = UNSET
        if not isinstance(self.wheels, Unset):
            wheels = self.wheels.to_dict()

        relays: dict[str, Any] | Unset = UNSET
        if not isinstance(self.relays, Unset):
            relays = self.relays.to_dict()

        temperature_sensor: dict[str, Any] | Unset = UNSET
        if not isinstance(self.temperature_sensor, Unset):
            temperature_sensor = self.temperature_sensor.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if wheels is not UNSET:
            field_dict["wheels"] = wheels
        if relays is not UNSET:
            field_dict["relays"] = relays
        if temperature_sensor is not UNSET:
            field_dict["temperature_sensor"] = temperature_sensor

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.pandora_state_relays import PandoraStateRelays
        from ..models.pandora_state_wheels import PandoraStateWheels
        from ..models.temperature_sensor_state import TemperatureSensorState

        d = dict(src_dict)
        _wheels = d.pop("wheels", UNSET)
        wheels: PandoraStateWheels | Unset
        if isinstance(_wheels, Unset):
            wheels = UNSET
        else:
            wheels = PandoraStateWheels.from_dict(_wheels)

        _relays = d.pop("relays", UNSET)
        relays: PandoraStateRelays | Unset
        if isinstance(_relays, Unset):
            relays = UNSET
        else:
            relays = PandoraStateRelays.from_dict(_relays)

        _temperature_sensor = d.pop("temperature_sensor", UNSET)
        temperature_sensor: TemperatureSensorState | Unset
        if isinstance(_temperature_sensor, Unset):
            temperature_sensor = UNSET
        else:
            temperature_sensor = TemperatureSensorState.from_dict(_temperature_sensor)

        pandora_state = cls(
            wheels=wheels,
            relays=relays,
            temperature_sensor=temperature_sensor,
        )

        pandora_state.additional_properties = d
        return pandora_state

    @property
    def additional_keys(self) -> list[str]:
        return list(self.additional_properties.keys())

    def __getitem__(self, key: str) -> Any:
        return self.additional_properties[key]

    def __setitem__(self, key: str, value: Any) -> None:
        self.additional_properties[key] = value

    def __delitem__(self, key: str) -> None:
        del self.additional_properties[key]

    def __contains__(self, key: str) -> bool:
        return key in self.additional_properties
