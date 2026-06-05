from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.raspi_server_get_status_response_raspi_server_get_status import (
    RaspiServerGetStatusResponseRaspiServerGetStatus,
)
from ...types import Response


def _get_kwargs() -> dict[str, Any]:

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/raspi-server/status",
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> RaspiServerGetStatusResponseRaspiServerGetStatus | None:
    if response.status_code == 200:
        response_200 = RaspiServerGetStatusResponseRaspiServerGetStatus.from_dict(response.json())

        return response_200

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[RaspiServerGetStatusResponseRaspiServerGetStatus]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
) -> Response[RaspiServerGetStatusResponseRaspiServerGetStatus]:
    """Get Status

     Get the current status of the lin_acts.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[RaspiServerGetStatusResponseRaspiServerGetStatus]
    """

    kwargs = _get_kwargs()

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient | Client,
) -> RaspiServerGetStatusResponseRaspiServerGetStatus | None:
    """Get Status

     Get the current status of the lin_acts.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        RaspiServerGetStatusResponseRaspiServerGetStatus
    """

    return sync_detailed(
        client=client,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
) -> Response[RaspiServerGetStatusResponseRaspiServerGetStatus]:
    """Get Status

     Get the current status of the lin_acts.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[RaspiServerGetStatusResponseRaspiServerGetStatus]
    """

    kwargs = _get_kwargs()

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
) -> RaspiServerGetStatusResponseRaspiServerGetStatus | None:
    """Get Status

     Get the current status of the lin_acts.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        RaspiServerGetStatusResponseRaspiServerGetStatus
    """

    return (
        await asyncio_detailed(
            client=client,
        )
    ).parsed
