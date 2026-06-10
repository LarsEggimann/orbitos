from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="PandoraWheelState")


@_attrs_define
class PandoraWheelState:
    """
    Attributes:
        status (str | Unset):  Default: 'unknown'.
        position (float | None | Unset):
        velocity (float | None | Unset):
    """

    status: str | Unset = "unknown"
    position: float | None | Unset = UNSET
    velocity: float | None | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        status = self.status

        position: float | None | Unset
        if isinstance(self.position, Unset):
            position = UNSET
        else:
            position = self.position

        velocity: float | None | Unset
        if isinstance(self.velocity, Unset):
            velocity = UNSET
        else:
            velocity = self.velocity

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if status is not UNSET:
            field_dict["status"] = status
        if position is not UNSET:
            field_dict["position"] = position
        if velocity is not UNSET:
            field_dict["velocity"] = velocity

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        status = d.pop("status", UNSET)

        def _parse_position(data: object) -> float | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(float | None | Unset, data)

        position = _parse_position(d.pop("position", UNSET))

        def _parse_velocity(data: object) -> float | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(float | None | Unset, data)

        velocity = _parse_velocity(d.pop("velocity", UNSET))

        pandora_wheel_state = cls(
            status=status,
            position=position,
            velocity=velocity,
        )

        pandora_wheel_state.additional_properties = d
        return pandora_wheel_state

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
