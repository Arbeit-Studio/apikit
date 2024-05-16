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
        self.token = token
        self.obfuscated_token = "*" * (len(self.token) - 4) + self.token[-4:]

    def authorize(self, session: HttpSession) -> HttpSession:
        session.auth = BearerTokenAuth(self.token)
        return session

    def __str__(self) -> str:
        return f"{type(self).__name__}({self.obfuscated_token})"


class DefaultHttpSession(Session, HttpSession):
    """Extensão da Session do requests utilizada para requisições"""

    def __init__(self, read_timeout: int = None) -> None:
        read_timeout = read_timeout or 60
        # setup cache
        super().__init__()
        # setup headers padrões
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

        # setup timeout
        self.request = partial(self.request, timeout=(3.5, read_timeout))  # type: ignore
        logger.debug(f"Initialized: {self}")

    @classmethod
    def from_context(
        cls, *, context, authorizer: Authorizer = None, read_timeout: int = None  # type: ignore
    ) -> "DefaultHttpSession":
        """Retorna o a instância do context ou cria uma nova se não existir"""
        context_key = cls._context_key(read_timeout)
        session = context.setdefault(
            context_key,
            cls._initialize(authorizer, read_timeout),
        )
        logger.debug(
            f"Pegando {cls.__name__} com timeout={read_timeout} do app context."
        )
        return session

    @classmethod
    def _initialize(cls, authorizer, read_timeout: int = None):
        read_timeout = read_timeout or 60
        if authorizer is not None:
            return authorizer.authorize(cls(read_timeout=read_timeout))
        return cls(read_timeout=read_timeout)

    @classmethod
    def from_app_context_or_new(cls, **params) -> "DefaultHttpSession":
        """Retorna o a instância do app context ou cria uma nova se não existir"""
        try:
            from flask import current_app

            return cls.from_context(context=current_app, **params)
        except:
            return cls._initialize(**params)

    @classmethod
    def _context_key(cls, salt):
        return cls.__name__ + str(salt)


class DefaultCachedHttpSession(CachedSession, DefaultHttpSession):
    """Session HTTP com cache"""

    def __init__(self, read_timeout: int = None) -> None:
        # setup cache

        super().__init__(
            cache_name="default_api_cache",
            backend="sqlite",
            expire_after=60 * 30,  # 1 minuto * 30 = 30 minutos
            stale_if_error=True,
            stale_while_revalidate=True,
            cache_control=True,
            read_timeout=read_timeout or 60,
        )
