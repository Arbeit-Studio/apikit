from typing import Any
from unittest.mock import patch

import pytest
import requests

from apikit.default import (
    DefaultHTTPRequestAdapter,
    DefaultHTTPRequestGateway,
    DefaultHTTPResponseAdapter,
)
from apikit.protocols import HTTPMethod
from apikit.session import DefaultHttpSession, StaticTokenSessionAuthorizer
from apikit.specs import HTTPGatewayGETSpec, HTTPGatewayPOSTSpec, HTTPGatewaySpec


def test_http_gateway_spec_init_with_none_url():
    with pytest.raises(AssertionError):
        HTTPGatewaySpec(url=None, method=HTTPMethod.GET)


def test_http_gateway_spec_init_with_no_url():
    with pytest.raises(AssertionError):
        HTTPGatewaySpec(method=HTTPMethod.GET)


def test_http_gateway_spec_init_with_none_method():
    with pytest.raises(AssertionError):
        HTTPGatewaySpec(url="https://test.com", method=None)


def test_http_gateway_spec_init_no_method():
    with pytest.raises(AssertionError):
        HTTPGatewaySpec(url="https://test.com")


def test_http_gateway_spec_init_with_default_http_request():
    spec = HTTPGatewaySpec(url="https://test.com", method=HTTPMethod.GET)
    assert isinstance(spec.gateway, DefaultHTTPRequestGateway)


def test_http_gateway_spec_init_with_default_http_request_adapter():
    spec = HTTPGatewaySpec(url="https://test.com", method=HTTPMethod.GET)
    assert isinstance(spec.gateway.request_adapter, DefaultHTTPRequestAdapter)


def test_http_gateway_spec_init_with_default_http_response_adapter():
    spec = HTTPGatewaySpec(url="https://test.com", method=HTTPMethod.GET)
    assert isinstance(spec.gateway.response_adapter, DefaultHTTPResponseAdapter)


def test_http_gateway_spec_init_with_override_http_request_adapter_class():
    class TestHTTPRequestAdapter(DefaultHTTPRequestAdapter): ...

    spec = HTTPGatewaySpec(
        url="https://test.com",
        method=HTTPMethod.GET,
        request_adapter=TestHTTPRequestAdapter,
    )
    assert isinstance(spec.gateway.request_adapter, TestHTTPRequestAdapter)


def test_http_gateway_spec_init_with_override_http_response_adapter_class():
    class TestHTTPResponseAdapter(DefaultHTTPResponseAdapter): ...

    spec = HTTPGatewaySpec(
        url="https://test.com",
        method=HTTPMethod.GET,
        response_adapter=TestHTTPResponseAdapter,
    )
    assert isinstance(spec.gateway.response_adapter, TestHTTPResponseAdapter)


def test_http_gateway_spec_init_with_override_http_request_adapter_instance():
    class TestHTTPRequestAdapter(DefaultHTTPRequestAdapter): ...

    spec = HTTPGatewaySpec(
        url="https://test.com",
        method=HTTPMethod.GET,
        request_adapter=TestHTTPRequestAdapter(),
    )
    assert isinstance(spec.gateway.request_adapter, TestHTTPRequestAdapter)


def test_http_gateway_spec_init_with_override_http_response_adapter_instance():
    class TestHTTPResponseAdapter(DefaultHTTPResponseAdapter): ...

    spec = HTTPGatewaySpec(
        url="https://test.com",
        method=HTTPMethod.GET,
        response_adapter=TestHTTPResponseAdapter(),
    )
    assert isinstance(spec.gateway.response_adapter, TestHTTPResponseAdapter)


def test_http_gateway_spec_get():
    class TestClient:
        test_request = HTTPGatewaySpec(url="https://test.com", method=HTTPMethod.GET)

    test_client = TestClient()
    assert isinstance(test_client.test_request, DefaultHTTPRequestGateway)


def test_http_gateway_get_spec_init():
    spec = HTTPGatewayGETSpec(url="https://test.com")
    assert spec.gateway.method == HTTPMethod.GET


def test_http_gateway_post_spec_init():
    spec = HTTPGatewayPOSTSpec(url="https://test.com")
    assert spec.gateway.method == HTTPMethod.POST


def test_http_gateway_spec_init_with_authorizer():
    class TestHTTPGatewaySpec(HTTPGatewaySpec):
        url = "https://test.com/test"
        method = HTTPMethod.GET
        authorizer = StaticTokenSessionAuthorizer(token="test_token")

    spec = TestHTTPGatewaySpec()
    assert spec.gateway.session.auth.token == "test_token"


def test_http_gateway_spec_init_with_base_url():
    class TestHTTPGatewaySpec(
        HTTPGatewaySpec,
    ):
        base_url = "https://test.com"
        method = HTTPMethod.GET

    spec = TestHTTPGatewaySpec(url="/test")
    assert spec.gateway.url == "https://test.com/test"


def test_http_gateway_spec_init_with_invalid_url():
    class TestHTTPGatewaySpec(
        HTTPGatewaySpec,
    ):
        method = HTTPMethod.GET

    with pytest.raises(ValueError):
        spec = TestHTTPGatewaySpec(url="/test")


def test_http_gateway_spec_inheritance_with_with_base_url():
    class TestHTTPGatewaySpec(
        HTTPGatewaySpec,
    ):
        base_url = "https://test.com"
        method = HTTPMethod.GET
        response_model = object

    class TestChildHTTPGatewaySpec(TestHTTPGatewaySpec): ...

    spec = TestChildHTTPGatewaySpec(url="/test")
    assert spec.gateway.url == "https://test.com/test"


def test_http_gateway_spec_inheritance_with_method_attribute():
    class TestHTTPGatewaySpec(
        HTTPGatewaySpec,
    ):
        method = HTTPMethod.GET

    class TestChildHTTPGatewaySpec(TestHTTPGatewaySpec): ...

    spec = TestChildHTTPGatewaySpec(url="https://test.com")
    assert spec.gateway.method == HTTPMethod.GET


def test_http_gateway_spec_inheritance_with_request_adapter_attribute():
    class TestDefaultHTTPRequestAdapter(DefaultHTTPRequestAdapter): ...

    class TestHTTPGatewaySpec(
        HTTPGatewaySpec,
    ):
        method = HTTPMethod.GET
        request_adapter = TestDefaultHTTPRequestAdapter

    class TestChildHTTPGatewaySpec(TestHTTPGatewaySpec): ...

    spec = TestChildHTTPGatewaySpec(url="https://test.com")
    assert isinstance(spec.gateway.request_adapter, TestDefaultHTTPRequestAdapter)


def test_http_gateway_spec_inheritance_with_response_adapter_attribute():
    class TestDefaultHTTPResponseAdapter(DefaultHTTPResponseAdapter): ...

    class TestHTTPGatewaySpec(
        HTTPGatewaySpec,
    ):
        method = HTTPMethod.GET
        response_adapter = TestDefaultHTTPResponseAdapter

    class TestChildHTTPGatewaySpec(TestHTTPGatewaySpec): ...

    spec = TestChildHTTPGatewaySpec(url="https://test.com")
    assert isinstance(spec.gateway.response_adapter, TestDefaultHTTPResponseAdapter)


def test_http_gateway_spec_inheritance_with_authorizer():
    class TestHTTPGatewaySpec(HTTPGatewaySpec):
        url = "https://test.com/test"
        method = HTTPMethod.GET
        authorizer = StaticTokenSessionAuthorizer(token="test_token")

    class TestChildHTTPGatewaySpec(TestHTTPGatewaySpec): ...

    spec = TestChildHTTPGatewaySpec()
    assert spec.gateway.session.auth.token == "test_token"


def test_http_gateway_spec_inheritance_with_session_attribute():
    class TestHTTPSession(DefaultHttpSession): ...

    class TestHTTPGatewaySpec(
        HTTPGatewaySpec,
    ):
        method = HTTPMethod.GET
        session = TestHTTPSession

    class TestChildHTTPGatewaySpec(TestHTTPGatewaySpec): ...

    spec = TestChildHTTPGatewaySpec(url="https://test.com")
    assert isinstance(spec.gateway.session, TestHTTPSession)


def test_http_gateway_spec_inheritance_with_gateway_attribute():
    class TestHTTPGateway(DefaultHTTPRequestGateway): ...

    class TestHTTPGatewaySpec(
        HTTPGatewaySpec,
    ):
        method = HTTPMethod.GET
        gateway = TestHTTPGateway

    class TestChildHTTPGatewaySpec(TestHTTPGatewaySpec): ...

    spec = TestChildHTTPGatewaySpec(url="https://test.com")
    assert isinstance(spec.gateway, TestHTTPGateway)


@pytest.mark.parametrize(
    "read_timeout, expected",
    [(120, (3.5, 120)), (60, (3.5, 60)), (None, (3.5, None)), (5, (3.5, 5))],
)
def test_http_gateway_spec_with_timeout_attribute(read_timeout, expected):
    with patch.object(DefaultHttpSession, "request") as mock_request:

        class TestTimeoutHTTPGatewaySpec(HTTPGatewaySpec):
            url = "http://test.com"
            method = HTTPMethod.GET
            session = DefaultHttpSession
            timeout = read_timeout

        class TestTimeoutClient:
            test_timeout_request_spec = TestTimeoutHTTPGatewaySpec()

        test_timeout_client = TestTimeoutClient()

        test_timeout_client.test_timeout_request_spec({})
        mock_request.assert_called_once_with(
            method="GET",
            url="http://test.com",
            headers=None,
            timeout=expected,
            params={},
        )
