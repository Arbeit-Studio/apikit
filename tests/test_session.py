from unittest.mock import Mock

import pytest
from requests import Request

from apikit.session import (
    BearerTokenAuth,
    DefaultCachedHttpSession,
    DefaultHttpSession,
    StaticTokenSessionAuthorizer,
)


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

    test_session = DefaultHttpSession.from_context(context=Mock())
    test_session_key = DefaultHttpSession._context_key()
    assert hasattr(test_session, test_session_key)


def test_default_http_session__initialize_without_authorizer():
    session = DefaultHttpSession._initialize(
        authorizer=None,
    )
    assert session.auth is None


def test_default_http_session__initialize_with_authorizer():
    test_authorizer = StaticTokenSessionAuthorizer(token="test_token")
    session = DefaultHttpSession._initialize(authorizer=test_authorizer)
    assert session.auth


def test_default_cached_http_session():
    session = DefaultCachedHttpSession()
    assert session.cache
