import json
from dataclasses import asdict, dataclass, is_dataclass
from unittest.mock import create_autospec

import pytest
import responses
from pydantic import BaseModel, TypeAdapter
from requests import HTTPError, Response, Session
from requests.models import RequestEncodingMixin
from typing_extensions import TypedDict

from apikit.default import (
    DefaultHTTPRequestAdapter,
    DefaultHTTPRequestGateway,
    DefaultHTTPResponseAdapter,
)
from apikit.protocols import HTTPMethod, HTTPResponse

# region stubs, fixtures e helpers


# BaseModel User dummies
class BMUser(BaseModel):
    name: str
    id: int


bmuser = BMUser(name="Testinho", id=777)
bmuser_response = create_autospec(HTTPResponse)
bmuser_response.content = BMUser(name="Testinho", id=777).model_dump_json()


# Dataclass User dummies
@dataclass
class DCUser:
    name: str
    id: int


dcuser = DCUser("Testinho", 777)
dcuser_response = create_autospec(HTTPResponse)
dcuser_response.content = json.dumps(asdict(dcuser)).encode()


# TypedDict User dummies
class TDUser(TypedDict):
    name: str
    id: int


tduser = TDUser(name="Testinho", id=777)
tduser_response = create_autospec(HTTPResponse)
tduser_response.content = json.dumps(tduser).encode()


response_500 = Response()
response_500.status_code = 500
response_500.reason = "Test Server Error"
response_500.url = "http://test.com/user"

response_400 = Response()
response_400.status_code = 400
response_400.reason = "Test Client Error"
response_500.url = "http://test.com/user"


none_response = create_autospec(HTTPResponse)
none_response.content = None


def to_dict(instance):
    if isinstance(instance, BaseModel):
        return instance.model_dump()
    if isinstance(instance, dict):
        return instance
    if is_dataclass(instance):
        return asdict(instance)


@pytest.fixture(scope="module")
def url():
    return "http://test.com/user"


@pytest.fixture
def session():
    return Session()


@pytest.fixture(scope="module")
def headers():
    return {"Content-Type": "application/json"}


# endregion

# region HttpResponseAdapter Tests


@pytest.mark.unit
@pytest.mark.parametrize(
    "model, adapted, response",
    [
        (BMUser, bmuser, bmuser_response),
        (DCUser, dcuser, dcuser_response),
        (TDUser, tduser, tduser_response),
        (None, none_response, none_response),
        (None, tduser_response, tduser_response),
    ],
)
def test_http_response_adapter(model, adapted, response):
    adapter = DefaultHTTPResponseAdapter(model)
    assert adapter.adapt(response) == adapted


@pytest.mark.unit
@pytest.mark.parametrize(
    "model, response",
    [(TDUser, response_500), (TDUser, response_400), (None, response_500)],
)
def test_http_response_adapter_with_400_or_more_response(model, response):
    adapter = DefaultHTTPResponseAdapter(model)
    with pytest.raises(HTTPError):
        adapter.adapt(response)


# endregion

# region HttpRequestAdapter Tests


@pytest.mark.unit
@pytest.mark.parametrize(
    "model, instance",
    [
        (BMUser, bmuser),
        (DCUser, dcuser),
        (TDUser, tduser),
        (None, None),
    ],
)
def test_http_request_adapter_for_post(model, instance, url, headers):
    adapter = DefaultHTTPRequestAdapter(model)
    method = HTTPMethod.POST
    request = adapter.adapt(url=url, method=method, data=instance, headers=headers)
    assert request["url"] == url
    assert request["method"] == method.value
    assert request["json"] == to_dict(instance)
    assert headers.items() <= request["headers"].items()


@pytest.mark.unit
@pytest.mark.parametrize(
    "model, instance",
    [
        (BMUser, bmuser),
        (DCUser, dcuser),
        (TDUser, tduser),
        (None, None),
    ],
)
def test_http_request_adapter_for_get(model, instance, url, headers):
    adapter = DefaultHTTPRequestAdapter(model)
    method = HTTPMethod.GET
    request = adapter.adapt(url=url, method=method, data=instance, headers=headers)
    assert request["url"] == url
    assert request["params"] == to_dict(instance)
    assert request["method"] == method.value
    assert headers.items() <= request["headers"].items()


# endregion

# region HttpRequestGateway Tests


@pytest.mark.unit
@pytest.mark.parametrize(
    "model, instance",
    [
        (BMUser, bmuser),
        (DCUser, dcuser),
        (TDUser, tduser),
        (None, None),
    ],
)
def test_http_request_gateway_prepare_get(model, instance, session, url, headers):
    method = HTTPMethod.GET
    gateway = DefaultHTTPRequestGateway(
        session=session,
        url=url,
        method=method,
        request_adapter=DefaultHTTPRequestAdapter(model),
        response_adapter=...,
        headers=headers,
    )
    request = gateway.prepare(instance)
    assert request["url"] == url
    assert request["params"] == to_dict(instance)
    assert request["method"] == method.value
    assert headers.items() <= request["headers"].items()


@pytest.mark.unit
@pytest.mark.parametrize(
    "model, instance",
    [
        (BMUser, bmuser),
        (DCUser, dcuser),
        (TDUser, tduser),
        (None, None),
    ],
)
def test_http_request_gateway_prepare_post(model, instance, session, url, headers):
    method = HTTPMethod.POST
    gateway = DefaultHTTPRequestGateway(
        session=session,
        url=url,
        method=method,
        request_adapter=DefaultHTTPRequestAdapter(model),
        response_adapter=...,
        headers=headers,
    )
    request = gateway.prepare(instance)
    assert request["url"] == url
    assert request["method"] == method.value
    assert request["json"] == to_dict(instance)
    assert headers.items() <= request["headers"].items()


@pytest.mark.unit
@pytest.mark.parametrize(
    "model, received, response",
    [
        (BMUser, bmuser, bmuser_response),
        (DCUser, dcuser, dcuser_response),
        (TDUser, tduser, tduser_response),
        (None, tduser_response, tduser_response),
    ],
)
def test_http_request_gateway_receive_post(
    model, received, response, session, url, headers
):
    method = HTTPMethod.POST
    gateway = DefaultHTTPRequestGateway(
        session=session,
        url=url,
        method=method,
        request_adapter=...,
        response_adapter=DefaultHTTPResponseAdapter(model),
        headers=headers,
    )
    assert gateway.ingress(response) == received


@pytest.mark.unit
@pytest.mark.parametrize(
    "model, received, response",
    [
        (BMUser, bmuser, bmuser_response),
        (DCUser, dcuser, dcuser_response),
        (TDUser, tduser, tduser_response),
        (None, tduser_response, tduser_response),
    ],
)
def test_http_request_gateway_receive_get(
    model, received, response, session, url, headers
):
    method = HTTPMethod.GET
    gateway = DefaultHTTPRequestGateway(
        session=session,
        url=url,
        method=method,
        request_adapter=...,
        response_adapter=DefaultHTTPResponseAdapter(model),
        headers=headers,
    )
    assert gateway.ingress(response) == received


@pytest.mark.unit
@pytest.mark.parametrize(
    "model, instance",
    [
        (BMUser, bmuser),
        (DCUser, dcuser),
        (TDUser, tduser),
        (None, None),
    ],
)
def test_http_request_gateway_execute_get(model, instance, session, url, headers):
    method = HTTPMethod.GET
    gateway = DefaultHTTPRequestGateway(
        session=session,
        url=url,
        method=method,
        request_adapter=DefaultHTTPRequestAdapter(model),
        response_adapter=DefaultHTTPResponseAdapter(model),
        headers=headers,
    )
    response_if_none_model = responses.get(url, json=to_dict(instance))
    response = gateway(instance)
    # return the request object if the model is None
    assert response == instance or response_if_none_model


@pytest.mark.unit
@pytest.mark.parametrize(
    "model, instance",
    [
        (BMUser, bmuser),
        (DCUser, dcuser),
        (TDUser, tduser),
        (None, None),
    ],
)
def test_http_request_gateway_execute_post(model, instance, session, url, headers):
    method = HTTPMethod.POST
    gateway = DefaultHTTPRequestGateway(
        session=session,
        url=url,
        method=method,
        request_adapter=DefaultHTTPRequestAdapter(model),
        response_adapter=DefaultHTTPResponseAdapter(model),
        headers=headers,
    )
    response_if_none_model = responses.post(url, json=to_dict(instance))
    response = gateway(instance)
    # se o model é nulo o retorno é a própira response
    assert response == instance or response_if_none_model


# endregion

# region Timeout Tests


# endregion
