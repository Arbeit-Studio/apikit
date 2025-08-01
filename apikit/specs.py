from functools import partialmethod
from inspect import isclass
from typing import Optional, Union
from urllib.parse import urlparse

from typing_extensions import dataclass_transform

from apikit.default import (
    DefaultHTTPRequestAdapter,
    DefaultHTTPRequestGateway,
    DefaultHTTPResponseAdapter,
)
from apikit.protocols import (
    HTTPMethod,
    HTTPRequestAdapter,
    HTTPRequestGateway,
    HTTPResponseAdapter,
    HttpSession,
)
from apikit.session import DefaultHttpSession, StaticTokenSessionAuthorizer


def get_url(base_url, url):
    parsed_url = urlparse(url)
    parsed_base_url = urlparse(base_url)
    if not (
        (parsed_url.scheme and parsed_url.netloc)
        or (parsed_base_url.scheme and parsed_base_url.netloc)
    ):
        raise ValueError(
            "Either the base_url or url must be a valid URL with scheme and netloc."
        )
    if not (parsed_url.scheme and parsed_url.netloc):
        return base_url + url
    return url


def _init_fn(
    self,
    *,
    url: str = None,
    method: HTTPMethod = None,
    base_url: Optional[str] = "",
    timeout: Optional[int] = None,
    request_adapter: Union[HTTPRequestAdapter, type[HTTPRequestAdapter]] = None,
    response_adapter: Union[HTTPResponseAdapter, type[HTTPResponseAdapter]] = None,
    request_model=None,
    response_model=None,
    session: type[HttpSession] = None,
    authorizer: StaticTokenSessionAuthorizer = None,
    gateway: type[HTTPRequestGateway] = None,
    **kwargs,
):
    """
    Initializes the API specification object.

    All passed arguments are prioritized over class attributes. But, if not provided,
    class attributes are used, so we benefit from class inheritance to declare common
    attributes

    Despite having default values, url and method are required not to be None
    base_url is optional, but if not provided, url must be a full URL

    Args:
        url (str, optional): The URL for the API endpoint. Defaults to None.
        method (HTTPMethod, optional): The HTTP method for the API endpoint. Defaults to None.
        base_url (str, optional): The base URL for the API. Defaults to "".
        request_adapter (HTTPRequestAdapter, type[HTTPRequestAdapter], optional): The request adapter for the API. Defaults to None.
        response_adapter (HTTPResponseAdapter, type[HTTPResponseAdapter], optional): The response adapter for the API. Defaults to None.
        request_model (optional): The request model for the API. Defaults to None.
        response_model (optional): The response model for the API. Defaults to None.
        session (type[HttpSession], optional): The HTTP session for the API. Defaults to None.
        authorizer (StaticTokenSessionAuthorizer, optional): The authorizer for the API. Defaults to None.
        gateway (type[HTTPRequestGateway], optional): The gateway for the API. Defaults to None.
        **kwargs: Additional keyword arguments.

    Returns:
        The initialized gateway object.

    Raises:
        AssertionError: If required arguments are not provided.

    """
    # If gateway is already initialized, return it
    if gateway and not isclass(gateway):
        return gateway

    url = url or getattr(self, "url", None)
    assert url, "url must be provided"
    base_url = base_url or getattr(self, "base_url", None)
    url = get_url(base_url, url)

    method = method or getattr(self, "method", None)
    assert method, "method must be provided"

    request_model = request_model or getattr(self, "request_model", None)
    response_model = response_model or getattr(self, "response_model", None)

    request_adapter = (
        request_adapter
        or getattr(self, "request_adapter", None)
        or DefaultHTTPRequestAdapter
    )
    response_adapter = (
        response_adapter
        or getattr(self, "response_adapter", None)
        or DefaultHTTPResponseAdapter
    )
    session = session or getattr(self, "session", None) or DefaultHttpSession

    authorizer = authorizer or getattr(self, "authorizer", None)

    gateway = gateway or getattr(self, "gateway", None) or DefaultHTTPRequestGateway

    initialized_session = session.from_app_context_or_new(authorizer=authorizer)

    initialized_request_adapter = (
        request_adapter(model=request_model)
        if isclass(request_adapter)
        else request_adapter
    )

    initialized_response_adapter = (
        response_adapter(model=response_model)
        if isclass(response_adapter)
        else response_adapter
    )

    self.gateway = gateway(
        session=initialized_session,
        url=url,
        method=method,
        timeout=timeout,
        request_adapter=initialized_request_adapter,
        response_adapter=initialized_response_adapter,
    )


@dataclass_transform()
class MetaSpec(type):
    def __new__(metacls, name, bases, attrs):
        cls = super().__new__(metacls, name, bases, attrs)
        setattr(cls, "__init__", partialmethod(_init_fn, **attrs))
        return cls


class HTTPGatewaySpec(metaclass=MetaSpec):

    def __init__(
        self,
        *,
        url: str = None,
        method: HTTPMethod = None,
        base_url: Optional[str] = "",
        timeout: Optional[int] = None,
        request_adapter: Union[HTTPRequestAdapter, type[HTTPRequestAdapter]] = None,
        response_adapter: Union[HTTPResponseAdapter, type[HTTPResponseAdapter]] = None,
        request_model=None,
        response_model=None,
        session: type[HttpSession] = None,
        authorizer: StaticTokenSessionAuthorizer = None,
        gateway: type[HTTPRequestGateway] = None,
        **kwargs,
    ):
        _init_fn(
            self,
            url=url,
            method=method,
            base_url=base_url,
            timeout=timeout,
            request_adapter=request_adapter,
            response_adapter=response_adapter,
            request_model=request_model,
            response_model=response_model,
            session=session,
            authorizer=authorizer,
            gateway=gateway,
            **kwargs,
        )

    def __get__(self, instance, owner):
        return self.gateway

    def __set_name__(self, owner, name):
        self.name = name


class HTTPGatewayGETSpec(HTTPGatewaySpec):
    method = HTTPMethod.GET


class HTTPGatewayPOSTSpec(HTTPGatewaySpec):
    method = HTTPMethod.POST
