from http import HTTPStatus
from typing import Any
from urllib.parse import quote

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.base_response import BaseResponse
from ...models.http_validation_error import HTTPValidationError
from ...types import Response


def _get_kwargs(
    wheel_id: int,
) -> dict[str, Any]:

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/wheels/{wheel_id}/stop-reference-search".format(
            wheel_id=quote(str(wheel_id), safe=""),
        ),
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> BaseResponse | HTTPValidationError | None:
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
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[BaseResponse | HTTPValidationError]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    wheel_id: int,
    *,
    client: AuthenticatedClient | Client,
) -> Response[BaseResponse | HTTPValidationError]:
    """Stop Reference Search

     Stop the reference search for the wheel with the given ID.

    Args:
        wheel_id (int):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[BaseResponse | HTTPValidationError]
    """

    kwargs = _get_kwargs(
        wheel_id=wheel_id,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    wheel_id: int,
    *,
    client: AuthenticatedClient | Client,
) -> BaseResponse | HTTPValidationError | None:
    """Stop Reference Search

     Stop the reference search for the wheel with the given ID.

    Args:
        wheel_id (int):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        BaseResponse | HTTPValidationError
    """

    return sync_detailed(
        wheel_id=wheel_id,
        client=client,
    ).parsed


async def asyncio_detailed(
    wheel_id: int,
    *,
    client: AuthenticatedClient | Client,
) -> Response[BaseResponse | HTTPValidationError]:
    """Stop Reference Search

     Stop the reference search for the wheel with the given ID.

    Args:
        wheel_id (int):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[BaseResponse | HTTPValidationError]
    """

    kwargs = _get_kwargs(
        wheel_id=wheel_id,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    wheel_id: int,
    *,
    client: AuthenticatedClient | Client,
) -> BaseResponse | HTTPValidationError | None:
    """Stop Reference Search

     Stop the reference search for the wheel with the given ID.

    Args:
        wheel_id (int):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        BaseResponse | HTTPValidationError
    """

    return (
        await asyncio_detailed(
            wheel_id=wheel_id,
            client=client,
        )
    ).parsed
