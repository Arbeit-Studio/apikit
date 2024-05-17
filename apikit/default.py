from typing import Generic, Optional, Union
from pydantic import TypeAdapter
from requests import Request

from apikit.protocols import (
    Q,
    T,
    HTTPMethod,
    HTTPRequest,
    HTTPRequestAdapter,
    HTTPRequestGateway,
    HTTPResponse,
    HTTPResponseAdapter,
    HttpSession,
)


def is_like_get(method):
    return method in [HTTPMethod.GET, HTTPMethod.OPTIONS]


def is_like_post(method):
    return method in [HTTPMethod.POST, HTTPMethod.PUT, HTTPMethod.PATCH]


class DefaultHTTPResponseAdapter(HTTPResponseAdapter, Generic[Q]):
    """Adapts the given HTTPResponse to a instance of the model.
    Returns the entire response if model is None.
    Raises HTTPError if the status code of the response es greather than or equal to 400.

    Args:
        model Optional[type[Q]]: The type of object the adapter will try to parse from
        the request body. Defaults to None, returning the response object.
    """

    def __init__(self, model: Optional[type[Q]] = None):
        self.adapter = TypeAdapter(model) if model else None

    def adapt(self, response: HTTPResponse) -> Union[Q, HTTPResponse]:
        """Adapts the body or raises if status code is greater than or equal to 400.

        Args:
            response (HTTPResponse): The response to adapt from

        Raises:
            HTTPError: When the response status_code is greater than or equal to 400.

        Returns:
            Union[Q, HTTPResponse]: Return the instance of the model or the entire
            response if model is None.
        """
        response.raise_for_status()
        if self.adapter:
            return self.adapter.validate_json(response.content)
        return response


# TODO: Could we use any arbitrary object as model?
class DefaultHTTPRequestAdapter(HTTPRequestAdapter, Generic[T]):
    """Adapts the given arguments into a HTTPRequest.
    The data argument has a special treatment, depending on the method:
    If the method is GET like, data will be the request url query params.
    If the method is POST like, the data will be request body

    The model is compatible with dataclass and TypedDict from the std library, or
    BaseModel from pydantic.

    Usage:
        >>> user_data = {"name": "Johnny", "id": 777}
        >>> adapter = DefaultHttpRequestAdapter(model=User)
        >>> request = adapter.adapt(session=session, method=HTTPMethod.POST, url=url,
                data=user_data, headers=headers)

    Args:
        model Optional[type[T]]: The type of object the adapter will try to serialize. Defaults to None, meaning no data will be serialized.
    """

    def __init__(
        self,
        model: Optional[type[T]] = None,
    ):
        self.adapter = TypeAdapter(model)

    def adapt(
        self,
        *,
        session: HttpSession,
        method: HTTPMethod,
        url: str,
        data: Optional[T] = None,
        headers: Optional[dict] = None,
    ) -> HTTPRequest:
        kwargs = {"method": method.value, "url": url, "headers": headers}
        # It might have a optimization to do here if whe dump directly to JSON.
        adapted = self.adapter.dump_python(data, exclude_none=True, exclude_unset=True)
        if is_like_post(method):
            kwargs["json"] = adapted
        if is_like_get(method):
            kwargs["params"] = adapted
        return session.prepare_request(Request(**kwargs))


class DefaultHTTPRequestGateway(HTTPRequestGateway, Generic[T, Q]):
    """_summary_

    Args:
        session (HttpSession): To handle the request.
        url (str): Complete URL without the query params.
        method (HTTPMethod): GET, POST, PUT, etc.
        headers (Optional[dict], optional): The same key/values requests can handle.
        Defaults to None.
        request_adapter (Optional[HTTPRequestAdapter[type[T]]], optional): Model to
        serialize the data into query params from. Defaults to None.
        response_adapter (Optional[HTTPResponseAdapter[type[Q]]], optional): Model to
        parse the body response to. Defaults to None.
    """

    def __init__(
        self,
        *,
        session: HttpSession,
        url: str,
        method: HTTPMethod,
        headers: Optional[dict] = None,
        request_adapter: Optional[HTTPRequestAdapter[type[T]]] = None,
        response_adapter: Optional[HTTPResponseAdapter[type[Q]]] = None,
    ):
        self.session = session
        self.url = url
        self.method = method
        self.request_adapter = request_adapter or DefaultHTTPRequestAdapter()
        self.response_adapter = response_adapter or DefaultHTTPResponseAdapter()
        self.headers = headers

    def prepare(self, data: Optional[T] = None) -> HTTPRequest:
        return self.request_adapter.adapt(
            session=self.session,
            url=self.url,
            method=self.method,
            data=data,
            headers=self.headers,
        )

    def egress(self, request) -> HTTPResponse:
        return self.session.send(request)

    def ingress(self, response: HTTPResponse) -> Union[Q, HTTPResponse]:
        return self.response_adapter.adapt(response)

    def __call__(self, params: Optional[T] = None) -> Union[Q, HTTPResponse]:
        request = self.prepare(params)
        response = self.egress(request)
        return self.ingress(response)
