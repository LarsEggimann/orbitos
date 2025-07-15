from collections.abc import Mapping
from typing import Any, TypeVar, Union, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.lin_act_status import LinActStatus
from ..types import UNSET, Unset

T = TypeVar("T", bound="BusStatus")


@_attrs_define
class BusStatus:
    """
    Attributes:
        lin_act_id (int):
        status (LinActStatus):
        raw_value (Union[None, Unset, int]):
    """

    lin_act_id: int
    status: LinActStatus
    raw_value: Union[None, Unset, int] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        lin_act_id = self.lin_act_id

        status = self.status.value

        raw_value: Union[None, Unset, int]
        if isinstance(self.raw_value, Unset):
            raw_value = UNSET
        else:
            raw_value = self.raw_value

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "lin_act_id": lin_act_id,
                "status": status,
            }
        )
        if raw_value is not UNSET:
            field_dict["raw_value"] = raw_value

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        lin_act_id = d.pop("lin_act_id")

        status = LinActStatus(d.pop("status"))

        def _parse_raw_value(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        raw_value = _parse_raw_value(d.pop("raw_value", UNSET))

        bus_status = cls(
            lin_act_id=lin_act_id,
            status=status,
            raw_value=raw_value,
        )

        bus_status.additional_properties = d
        return bus_status

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
