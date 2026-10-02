import sys
from unittest.mock import patch

import pytest
from flask import Flask
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


def test_static_token_session_authorizer_equality():
    authorizer = StaticTokenSessionAuthorizer(token="test_token")
    same_token = StaticTokenSessionAuthorizer(token="test_token")
    other_token = StaticTokenSessionAuthorizer(token="other_token")
    assert authorizer == same_token
    assert hash(authorizer) == hash(same_token)
    assert authorizer != other_token
    assert authorizer != "test_token"


def test_bearer_token_auth():
    test_token = "test_token"
    auth = BearerTokenAuth(token=test_token)
    authenticated_request = auth(Request())
    assert f"Bearer {test_token}" in authenticated_request.headers["Authorization"]


def test_default_http_session_from_context_reuses_session():
    context = {}
    authorizer = StaticTokenSessionAuthorizer(token="test_token")
    first = DefaultHttpSession.from_context(context=context, authorizer=authorizer)
    second = DefaultHttpSession.from_context(context=context, authorizer=authorizer)
    assert first is second
    assert first.auth.token == "test_token"


def test_default_http_session_from_context_initializes_once():
    context = {}
    with patch.object(
        DefaultHttpSession, "_initialize", wraps=DefaultHttpSession._initialize
    ) as initialize:
        DefaultHttpSession.from_context(context=context)
        DefaultHttpSession.from_context(context=context)
    assert initialize.call_count == 1


def test_default_http_session_from_context_one_session_per_authorizer():
    context = {}
    first = DefaultHttpSession.from_context(
        context=context, authorizer=StaticTokenSessionAuthorizer(token="first_token")
    )
    second = DefaultHttpSession.from_context(
        context=context, authorizer=StaticTokenSessionAuthorizer(token="second_token")
    )
    assert first is not second
    assert first.auth.token == "first_token"
    assert second.auth.token == "second_token"


def test_default_http_session_from_context_shares_session_for_equal_authorizers():
    context = {}
    first = DefaultHttpSession.from_context(
        context=context, authorizer=StaticTokenSessionAuthorizer(token="test_token")
    )
    second = DefaultHttpSession.from_context(
        context=context, authorizer=StaticTokenSessionAuthorizer(token="test_token")
    )
    assert first is second


def test_default_http_session_from_context_unhashable_authorizer():
    class UnhashableAuthorizer:
        __hash__ = None

        def authorize(self, session):
            return session

    context = {}
    authorizer = UnhashableAuthorizer()
    first = DefaultHttpSession.from_context(context=context, authorizer=authorizer)
    second = DefaultHttpSession.from_context(context=context, authorizer=authorizer)
    assert first is not second


def test_default_http_session_from_context_one_session_per_class():
    class OtherHttpSession(DefaultHttpSession): ...

    context = {}
    first = DefaultHttpSession.from_context(context=context)
    second = OtherHttpSession.from_context(context=context)
    assert first is not second
    assert isinstance(second, OtherHttpSession)


def test_default_http_session_from_app_context_or_new_reuses_session_in_app_context():
    authorizer = StaticTokenSessionAuthorizer(token="test_token")
    with Flask(__name__).app_context():
        first = DefaultHttpSession.from_app_context_or_new(authorizer=authorizer)
        second = DefaultHttpSession.from_app_context_or_new(authorizer=authorizer)
    assert first is second


def test_default_http_session_from_app_context_or_new_one_session_per_app_context():
    app = Flask(__name__)
    with app.app_context():
        first = DefaultHttpSession.from_app_context_or_new()
    with app.app_context():
        second = DefaultHttpSession.from_app_context_or_new()
    assert first is not second


def test_default_http_session_from_app_context_or_new_outside_app_context():
    first = DefaultHttpSession.from_app_context_or_new()
    second = DefaultHttpSession.from_app_context_or_new()
    assert first is not second


def test_default_http_session_from_app_context_or_new_without_flask(monkeypatch):
    monkeypatch.setitem(sys.modules, "flask", None)
    first = DefaultHttpSession.from_app_context_or_new()
    second = DefaultHttpSession.from_app_context_or_new()
    assert first is not second


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
