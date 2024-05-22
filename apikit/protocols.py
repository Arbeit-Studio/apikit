from enum import Enum
from typing import Any, Callable, Generic, Optional, Protocol, TypeVar, Union
from typing_extensions import Self

T = TypeVar("T", contravariant=True)
Q = TypeVar("Q", covariant=True)


class HTTPMethod(Enum):
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    PATCH = "PATCH"
    OPTIONS = "OPTIONS"


class HTTPRequest(Protocol):
    url: str
    method: HTTPMethod
    body: bytes
    headers: dict


class Authorizer(Protocol):

    def __init__(self, token: str) -> None:
        raise NotImplementedError  # pragma: no cover

    def authorize(self, session: "HttpSession") -> "HttpSession":
        raise NotImplementedError  # pragma: no cover


class HttpSession(Protocol):
    auth: Callable

    def get(self, url, **kwargs):
        raise NotImplementedError  # pragma: no cover

    def post(self, url, data=None, json=None, **kwargs):
        raise NotImplementedError  # pragma: no cover

    def put(self, url, data=None, **kwargs):
        raise NotImplementedError  # pragma: no cover

    def delete(self, url, **kwargs):
        raise NotImplementedError  # pragma: no cover

    def send(self, request: HTTPRequest):
        raise NotImplemented  # pragma: no cover

    def prepare_request(self, request: HTTPRequest):
        raise NotImplemented  # pragma: no cover

    @classmethod
    def from_context(
        cls, *, context, authorizer: Optional[Authorizer] = None, read_timeout: int = None  # type: ignore
    ) -> Self:
        raise NotImplemented  # pragma: no cover

    @classmethod
    def from_app_context_or_new(cls, **params) -> Self:
        raise NotImplemented  # pragma: no cover


Feature = Callable[..., Any]


class HTTPResponse(Protocol):
    content: bytes

    def raise_for_status(self):
        raise NotImplementedError  # pragma: no cover


class HTTPResponseAdapter(Protocol, Generic[Q]):

    def adapt(self, response: HTTPResponse) -> Union[Q, HTTPResponse]:
        raise NotImplementedError  # pragma: no cover


class HTTPRequestAdapter(Protocol, Generic[T]):

    def adapt(
        self,
        *,
        session: HttpSession,
        url: str,
        method: HTTPMethod,
        data: Optional[T],
        headers: Optional[dict],
    ):
        raise NotImplemented  # pragma: no cover


class HTTPRequestGateway(Protocol, Generic[T, Q]):
    def __call__(self, params: Optional[T]) -> Union[Q, HTTPResponse]:
        raise NotImplementedError  # pragma: no cover
