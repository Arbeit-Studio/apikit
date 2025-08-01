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
        """Get one instance from the app context or create a new one and store there."""
        context_key = cls._context_key()
        session = context.setdefault(
            context_key,
            cls._initialize(authorizer),
        )
        logger.debug(f"Getting session {cls.__name__} from app context.")
        return session

    @classmethod
    def _initialize(cls, authorizer):
        if authorizer is not None:
            return authorizer.authorize(cls())
        return cls()

    @classmethod
    def from_app_context_or_new(cls, **params) -> "DefaultHttpSession":
        """Retorna o a instância do app context ou cria uma nova se não existir"""
        try:
            from flask import current_app

            return cls.from_context(context=current_app, **params)
        except:
            return cls._initialize(**params)

    @classmethod
    def _context_key(cls, salt=""):
        return cls.__name__ + str(salt)


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
