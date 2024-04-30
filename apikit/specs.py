from functools import partialmethod
from inspect import isclass
from typing import Union
from typing_extensions import dataclass_transform
from urllib.parse import urlparse
from apikit.protocols import (
    HTTPMethod,
    HTTPRequestAdapter,
    HTTPRequestGateway,
    HTTPResponseAdapter,
    HttpSession,
)
from apikit.session import (
    DefaultHttpSession,
    StaticTokenSessionAuthorizer,
)
from apikit.default import (
    DefaultHTTPRequestAdapter,
    DefaultHTTPRequestGateway,
    DefaultHTTPResponseAdapter,
)


def get_url(base_url, url):
    parsed_url = urlparse(url)
    if not (parsed_url.scheme and parsed_url.netloc):
        return base_url + url
    return url


def _init_fn(
    self,
    *,
    url: str,
    method: HTTPMethod,
    request_adapter: Union[
        HTTPRequestAdapter, type[HTTPRequestAdapter]
    ] = DefaultHTTPRequestAdapter,
    response_adapter: Union[
        HTTPResponseAdapter, type[HTTPResponseAdapter]
    ] = DefaultHTTPResponseAdapter,
    request_model=None,
    response_model=None,
    session: type[HttpSession] = DefaultHttpSession,
    authorizer: type[StaticTokenSessionAuthorizer] = StaticTokenSessionAuthorizer,
    request: type[HTTPRequestGateway] = DefaultHTTPRequestGateway,
    **kwargs,
):
    if isclass(request):
        assert url, "url must be provided"
        url = get_url(base_url=self.base_url, url=url)
        assert method, "method must be provided"

    initialized_session = session.from_app_context_or_new(
        autorizer=(authorizer(token=self.auth_token) if self.auth_token else None)
    )

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

    self.request = request(
        http_session=initialized_session,
        url=url,
        method=method,
        request_adapter=initialized_request_adapter,
        response_adapter=initialized_response_adapter,
    )


@dataclass_transform()
class MetaSpec(type):
    def __new__(metacls, name, bases, attrs, base_url="", auth_token=None):
        cls = super().__new__(metacls, name, bases, attrs)
        setattr(cls, "__init__", partialmethod(_init_fn, **attrs))
        cls.base_url = base_url
        cls.auth_token = auth_token
        return cls


class HTTPGatewaySpec(metaclass=MetaSpec):

    def __get__(self, instance, owner):
        return self.request

    def __set_name__(self, owner, name):
        self.name = name


class HTTPGatewayGETSpec(HTTPGatewaySpec):
    method = HTTPMethod.GET


class HTTPGatewayPOSTSpec(HTTPGatewaySpec):
    method = HTTPMethod.POST
