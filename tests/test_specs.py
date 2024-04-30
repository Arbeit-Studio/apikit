import pytest
from apikit.default import (
    DefaultHTTPRequestAdapter,
    DefaultHTTPRequestGateway,
    DefaultHTTPResponseAdapter,
)
from apikit.protocols import (
    HTTPMethod,
    HTTPRequestAdapter,
    HTTPResponseAdapter,
)
from apikit.specs import (
    HTTPGatewayGETSpec,
    HTTPGatewayPOSTSpec,
    HTTPGatewaySpec,
)


def test_http_gateway_spec_init_with_none_url():
    with pytest.raises(AssertionError):
        HTTPGatewaySpec(url=None, method=HTTPMethod.GET)


def test_http_gateway_spec_init_with_no_url():
    with pytest.raises(TypeError):
        HTTPGatewaySpec(method=HTTPMethod.GET)


def test_http_gateway_spec_init_with_none_method():
    with pytest.raises(AssertionError):
        HTTPGatewaySpec(url="https://test.com", method=None)


def test_http_gateway_spec_init_no_method():
    with pytest.raises(TypeError):
        HTTPGatewaySpec(url="https://test.com")


def test_http_gateway_spec_init_with_default_http_request():
    spec = HTTPGatewaySpec(url="https://test.com", method=HTTPMethod.GET)
    assert isinstance(spec.request, DefaultHTTPRequestGateway)


def test_http_gateway_spec_init_with_default_http_request_adapter():
    spec = HTTPGatewaySpec(url="https://test.com", method=HTTPMethod.GET)
    assert isinstance(spec.request.request_adapter, DefaultHTTPRequestAdapter)


def test_http_gateway_spec_init_with_default_http_response_adapter():
    spec = HTTPGatewaySpec(url="https://test.com", method=HTTPMethod.GET)
    assert isinstance(spec.request.response_adapter, DefaultHTTPResponseAdapter)


def test_http_gateway_spec_init_with_override_http_request_adapter_class():
    class TestHTTPRequestAdapter(HTTPRequestAdapter): ...

    spec = HTTPGatewaySpec(
        url="https://test.com",
        method=HTTPMethod.GET,
        request_adapter=TestHTTPRequestAdapter,
    )
    assert isinstance(spec.request.request_adapter, TestHTTPRequestAdapter)


def test_http_gateway_spec_init_with_override_http_response_adapter_class():
    class TestHTTPResponseAdapter(HTTPResponseAdapter): ...

    spec = HTTPGatewaySpec(
        url="https://test.com",
        method=HTTPMethod.GET,
        response_adapter=TestHTTPResponseAdapter,
    )
    assert isinstance(spec.request.response_adapter, TestHTTPResponseAdapter)


def test_http_gateway_spec_init_with_override_http_request_adapter_instance():
    class TestHTTPRequestAdapter(HTTPRequestAdapter): ...

    spec = HTTPGatewaySpec(
        url="https://test.com",
        method=HTTPMethod.GET,
        request_adapter=TestHTTPRequestAdapter(),
    )
    assert isinstance(spec.request.request_adapter, TestHTTPRequestAdapter)


def test_http_gateway_spec_init_with_override_http_response_adapter_instance():
    class TestHTTPResponseAdapter(HTTPResponseAdapter): ...

    spec = HTTPGatewaySpec(
        url="https://test.com",
        method=HTTPMethod.GET,
        response_adapter=TestHTTPResponseAdapter(),
    )
    assert isinstance(spec.request.response_adapter, TestHTTPResponseAdapter)


def test_http_gateway_spec_get():
    class TestClient:
        test_request = HTTPGatewaySpec(url="https://test.com", method=HTTPMethod.GET)

    test_client = TestClient()
    assert isinstance(test_client.test_request, DefaultHTTPRequestGateway)


def test_http_gateway_get_spec_init():
    spec = HTTPGatewayGETSpec(url="https://test.com")
    assert spec.request.method == HTTPMethod.GET


def test_http_gateway_post_spec_init():
    spec = HTTPGatewayPOSTSpec(url="https://test.com")
    assert spec.request.method == HTTPMethod.POST
