from http import HTTPStatus
from typing import Any, Optional, Union

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.base_response import BaseResponse
from ...models.http_validation_error import HTTPValidationError
from ...types import Response


def _get_kwargs(
    lin_act_id: int,
) -> dict[str, Any]:
    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": f"/raspi-server/{lin_act_id}/retract",
    }

    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[Union[BaseResponse, HTTPValidationError]]:
    if response.status_code == 200:
        response_200 = BaseResponse.from_dict(response.json())

        return response_200
    if response.status_code == 422:
        response_422 = HTTPValidationError.from_dict(response.json())

        return response_422
    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Response[Union[BaseResponse, HTTPValidationError]]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    lin_act_id: int,
    *,
    client: Union[AuthenticatedClient, Client],
) -> Response[Union[BaseResponse, HTTPValidationError]]:
    """Retract Lin Act

     Switch lin_act assigned to the given ID to the 'retract' position.

    Args:
        lin_act_id (int):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[BaseResponse, HTTPValidationError]]
    """

    kwargs = _get_kwargs(
        lin_act_id=lin_act_id,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    lin_act_id: int,
    *,
    client: Union[AuthenticatedClient, Client],
) -> Optional[Union[BaseResponse, HTTPValidationError]]:
    """Retract Lin Act

     Switch lin_act assigned to the given ID to the 'retract' position.

    Args:
        lin_act_id (int):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[BaseResponse, HTTPValidationError]
    """

    return sync_detailed(
        lin_act_id=lin_act_id,
        client=client,
    ).parsed


async def asyncio_detailed(
    lin_act_id: int,
    *,
    client: Union[AuthenticatedClient, Client],
) -> Response[Union[BaseResponse, HTTPValidationError]]:
    """Retract Lin Act

     Switch lin_act assigned to the given ID to the 'retract' position.

    Args:
        lin_act_id (int):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[BaseResponse, HTTPValidationError]]
    """

    kwargs = _get_kwargs(
        lin_act_id=lin_act_id,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    lin_act_id: int,
    *,
    client: Union[AuthenticatedClient, Client],
) -> Optional[Union[BaseResponse, HTTPValidationError]]:
    """Retract Lin Act

     Switch lin_act assigned to the given ID to the 'retract' position.

    Args:
        lin_act_id (int):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[BaseResponse, HTTPValidationError]
    """

    return (
        await asyncio_detailed(
            lin_act_id=lin_act_id,
            client=client,
        )
    ).parsed
