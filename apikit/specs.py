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


class HTTPGatewaySpec:
    # class-level defaults (todos opcionais)
    base_url: str = ""
    method: HTTPMethod = None
    timeout: int = None
    session: type[HttpSession] = DefaultHttpSession
    authorizer: StaticTokenSessionAuthorizer = None
    request_adapter = DefaultHTTPRequestAdapter
    response_adapter = DefaultHTTPResponseAdapter
    request_model = None
    response_model = None
    gateway: type[HTTPRequestGateway] = DefaultHTTPRequestGateway

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
        cls = type(self)

        # kwargs has priority -> them class attr -> them default
        _url = url or getattr(cls, "url", None)
        _method = method or getattr(cls, "method", None)
        _base_url = base_url or getattr(cls, "base_url", "") or ""
        _timeout = timeout or getattr(cls, "timeout", None)
        _request_adapter = request_adapter or getattr(
            cls, "request_adapter", DefaultHTTPRequestAdapter
        )
        _response_adapter = response_adapter or getattr(
            cls, "response_adapter", DefaultHTTPResponseAdapter
        )
        _request_model = request_model or getattr(cls, "request_model", None)
        _response_model = response_model or getattr(cls, "response_model", None)
        _session = session or getattr(cls, "session", DefaultHttpSession)
        _auth = authorizer or getattr(cls, "authorizer", None)
        _gateway = gateway or getattr(cls, "gateway", DefaultHTTPRequestGateway)

        assert _url, "url must be provided"
        assert _method, "method must be provided"

        _full_url = get_url(_base_url, _url)
        _session_instance = _session.from_app_context_or_new(authorizer=_auth)

        _initialized_request_adapter = (
            _request_adapter(model=_request_model)
            if isclass(_request_adapter)
            else _request_adapter
        )

        _initialized_response_adapter = (
            _response_adapter(model=_response_model)
            if isclass(_response_adapter)
            else _response_adapter
        )

        self._gateway = _gateway(
            session=_session_instance,
            url=_full_url,
            method=_method,
            timeout=_timeout,
            request_adapter=_initialized_request_adapter,
            response_adapter=_initialized_response_adapter,
        )

    def __get__(self, instance, owner):
        if instance is None:
            return self
        return self._gateway

    def __set_name__(self, owner, name):
        self.name = name


class HTTPGatewayGETSpec(HTTPGatewaySpec):
    method = HTTPMethod.GET


class HTTPGatewayPOSTSpec(HTTPGatewaySpec):
    method = HTTPMethod.POST
