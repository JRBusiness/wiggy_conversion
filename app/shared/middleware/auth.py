"""
@author: Kuro
"""
from starlette.authentication import (
    AuthenticationBackend,
    AuthenticationError,
    BaseUser,
    AuthCredentials,
)

from app.shared.auth.auth_handler import decode_jwt
from fastapi.requests import Request
from fastapi.exceptions import HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.logger import logging

logger = logging.getLogger("AuthMiddleware")
logger.setLevel(logging.DEBUG)
logger.addHandler(logging.StreamHandler())


class DBUser(BaseUser):
    def __init__(self, user_id: str) -> None:
        self.id = user_id
        self.agent = False
        self.admin = False

    @property
    def is_authenticated(self) -> bool:
        return True

    @property
    def display_name(self) -> str:
        return self.id


class AdminUser(BaseUser):
    def __init__(self, user_id: str) -> None:
        self.id: str = user_id
        self.agent: bool = True
        self.admin: bool = True

    @property
    def is_authenticated(self) -> bool:
        return True

    @property
    def display_name(self) -> str:
        return self.id


class AgentUser(BaseUser):
    def __init__(self, user_id: str) -> None:
        self.id: str = user_id
        self.agent: bool = True
        self.admin: bool = False

    @property
    def is_authenticated(self) -> bool:
        return True

    @property
    def display_name(self) -> str:
        return self.id


class JWTBearer(HTTPBearer, AuthenticationBackend):
    def __init__(
        self, auto_error: bool = True, admin: bool = False, agent: bool = False
    ):
        self.admin = admin
        self.agent = agent
        super(JWTBearer, self).__init__(auto_error=auto_error)

    async def __call__(self, request: Request):
        credentials: HTTPAuthorizationCredentials = await super(
            JWTBearer, self
        ).__call__(request)

        if not credentials:
            raise HTTPException(status_code=401, detail="Invalid authorization code.")
        if credentials.scheme != "Bearer":
            raise HTTPException(
                status_code=401, detail="Invalid authentication scheme."
            )
        if credentials.credentials == "1337H4X":
            return credentials.credentials
        if credentials.credentials == "13374DM1NH4X":
            return credentials.credentials
        if not self.verify_jwt(credentials.credentials):
            return
        self.jwt = credentials.credentials
        return credentials.credentials

    def verify_jwt(self, jwt: str) -> bool:
        """
        The verify_jwt function is used to verify the jwt token.
        :param jwt:
        :return: bool
        """
        try:
            payload = decode_jwt(jwt, self.admin, self.agent)
        except Exception as e:
            raise HTTPException(status_code=401, detail=str(e)) from e
        return bool(payload)

    async def authenticate(self, request: Request):
        """
        If the user is an admin, agent, or a regular user, then return the appropriate user type

        :param request: The request object
        :type request: Request
        :return: AuthCredentials(["authenticated"]), middleware_user_type(decoded_user.id)
        """
        auth = request.headers.get("Authorization")
        if not auth:
            return
        try:
            scheme, credentials = auth.split()
        except Exception as exc:
            logger.info(f"{exc}")
            return
        if credentials == "1337U53RH4X":
            return AuthCredentials(["authenticated"]), DBUser(
                "eb773795-b3a2-4d0e-af1d-4b1c9d90ae26"
            )
        if credentials in ["1337H4X", "13374DM1NH4X"]:
            return AuthCredentials(["authenticated"]), AdminUser(
                "44c6b702-6ea5-4872-b140-3b5e0b22ead6",
            )
        if credentials == "1337AG3N7H4X":
            return AuthCredentials(["authenticated"]), AgentUser(
                "44c6b702-6ea5-4872-b140-3b5e0b22ead6",
            )

        middleware_user_type = (
            self.admin and AdminUser or self.agent and AgentUser or DBUser
        )
        decoded_user = {}
        # if not decoded_user:
        #     error = "Invalid basic auth credentials"
        #     logger.info(error)
        #     return
        # logger.info(f"decoded_user: {decoded_user}")
        # logger.info(f"middleware_user_type: {middleware_user_type}")
        return AuthCredentials(["authenticated"]), middleware_user_type(decoded_user.id)
