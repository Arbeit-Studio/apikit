import logging
from functools import partial
from typing import Optional

from requests import PreparedRequest, Session
from requests.adapters import HTTPAdapter
from requests.auth import AuthBase
from requests.models import PreparedRequest
from requests.models import Response as Response
from requests_cache import CachedSession
from urllib3 import Retry
from urllib3.util.retry import Retry

from apikit.protocols import Authorizer, HttpSession

logger = logging.getLogger(__name__)

# Name of the dict, inside the context, that holds the sessions.
CONTEXT_SESSIONS_KEY = "apikit_http_sessions"


class BearerTokenAuth(AuthBase):
    def __init__(self, token: str) -> None:
        self.token = token

    def __call__(self, r: PreparedRequest) -> PreparedRequest:
        r.headers["Authorization"] = f"Bearer {self.token}"
        return r


class StaticTokenSessionAuthorizer(Authorizer):
    """Sets retrieve and set a BearerTokenAuth in the session's auth property"""

    def __init__(self, token: str) -> None:
        assert isinstance(token, str), "Token must be a string"
        self.token = token
        self.obfuscated_token = "*" * (len(self.token) - 4) + self.token[-4:]

    def authorize(self, session: HttpSession) -> HttpSession:
        session.auth = BearerTokenAuth(self.token)
        return session

    def __str__(self) -> str:
        return f"{type(self).__name__}({self.obfuscated_token})"

    # Equal tokens authorize a session the same way, so the authorizers are
    # interchangeable — and share a session in the app context.
    def __eq__(self, other) -> bool:
        if type(other) is not type(self):
            return NotImplemented
        return other.token == self.token

    def __hash__(self) -> int:
        return hash((type(self), self.token))


class DefaultHttpSession(Session, HttpSession):
    """Extensão da Session do requests utilizada para requisições"""

    def __init__(self) -> None:
        # setup cache
        super().__init__()
        # setup headers
        self.headers.update(
            {
                "Content-Type": "application/json",
                "Accept": "application/json",
                "User-Agent": "HTTP Gateway/1.0",
            }
        )
        # setup retry
        retry = Retry(total=3, backoff_factor=0.35)
        self.mount("https://", HTTPAdapter(max_retries=retry))
        self.mount("http://", HTTPAdapter(max_retries=retry))

        logger.debug(f"Initialized: {self}")

    @classmethod
    def from_context(
        cls, *, context, authorizer: Authorizer = None  # type: ignore
    ) -> "DefaultHttpSession":
        """Get one instance from the context or create a new one and store there.

        `context` is anything with `setdefault`, like `flask.g` or a dict. There
        is one session per session class and authorizer: equal authorizers (two
        `StaticTokenSessionAuthorizer` with the same token) share a session, and
        sessions with different credentials are never shared.
        """
        sessions = context.setdefault(CONTEXT_SESSIONS_KEY, {})
        context_key = cls._context_key(authorizer)
        try:
            session = sessions.get(context_key)
        except TypeError:
            # An unhashable authorizer can't be a key: no sharing for it.
            return cls._initialize(authorizer)
        if session is None:
            session = sessions[context_key] = cls._initialize(authorizer)
            logger.debug(f"Session {cls.__name__} stored in the context.")
        return session

    @classmethod
    def _initialize(cls, authorizer=None):
        if authorizer is not None:
            return authorizer.authorize(cls())
        return cls()

    @classmethod
    def from_app_context_or_new(cls, **params) -> "DefaultHttpSession":
        """Return the session stored in Flask's app context (`flask.g`).

        Outside an app context, or without Flask installed, return a new one.
        """
        try:
            from flask import g, has_app_context
        except ImportError:
            return cls._initialize(**params)
        if not has_app_context():
            return cls._initialize(**params)
        return cls.from_context(context=g, **params)

    @classmethod
    def _context_key(cls, authorizer=None):
        return (cls, authorizer)


class DefaultCachedHttpSession(CachedSession, DefaultHttpSession):
    """Session HTTP com cache"""

    def __init__(self) -> None:
        # setup cache

        super().__init__(
            cache_name="default_api_cache",
            backend="sqlite",
            expire_after=60 * 30,  # 30 minutes
            stale_if_error=True,
            stale_while_revalidate=True,
            cache_control=True,
        )
