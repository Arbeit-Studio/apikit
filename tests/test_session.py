from unittest.mock import Mock
import pytest
from requests import Request
from apikit.session import (
    BearerTokenAuth,
    DefaultCachedHttpSession,
    DefaultHttpSession,
    StaticTokenSessionAuthorizer,
)


@pytest.mark.parametrize(
    "read_timeout, expectativa",
    [(120, (3.5, 120)), (60, (3.5, 60)), (None, (3.5, 60)), (5, (3.5, 5))],
)
def test_default_http_session_timeout(read_timeout, expectativa):
    """Testa se a session é criada com o timeout informado ou default"""
    test_i4pro_http_session = DefaultHttpSession(read_timeout=read_timeout)
    assert test_i4pro_http_session.request.keywords["timeout"] == expectativa


def test_static_token_session_authorizer():
    test_token = "test_token"
    authorizer = StaticTokenSessionAuthorizer(token=test_token)
    session = DefaultHttpSession()
    authorizer.authorize(session=session)
    assert isinstance(session.auth, BearerTokenAuth)
    assert session.auth.token == test_token


def test_static_token_session_authorizer_obfuscated_token():
    test_token = "test_token"
    authorizer = StaticTokenSessionAuthorizer(token=test_token)
    assert str(authorizer) == "StaticTokenSessionAuthorizer(******oken)"


def test_bearer_token_auth():
    test_token = "test_token"
    auth = BearerTokenAuth(token=test_token)
    authenticated_request = auth(Request())
    assert f"Bearer {test_token}" in authenticated_request.headers["Authorization"]


def test_default_http_session_from_context():

    read_timeout = 90
    test_session = DefaultHttpSession.from_context(
        context=Mock(), read_timeout=read_timeout
    )
    test_session_key = DefaultHttpSession._context_key(read_timeout)
    assert hasattr(test_session, test_session_key)


def test_default_http_session__initialize_without_authorizer():
    session = DefaultHttpSession._initialize(authorizer=None, read_timeout=90)
    assert session.auth is None


def test_default_http_session__initialize_with_authorizer():
    test_authorizer = StaticTokenSessionAuthorizer(token="test_token")
    session = DefaultHttpSession._initialize(
        authorizer=test_authorizer, read_timeout=90
    )
    assert session.auth


def test_default_cached_http_session():
    session = DefaultCachedHttpSession()
    assert session.cache
