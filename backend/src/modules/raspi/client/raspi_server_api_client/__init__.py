"""A client library for accessing Raspi Server API"""

from .client import AuthenticatedClient, Client

__all__ = (
    "AuthenticatedClient",
    "Client",
)
