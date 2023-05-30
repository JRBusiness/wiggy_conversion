"""
@author: Kuro
"""
import contextlib
import time
from datetime import timedelta
from typing import Optional, Any

import jwt
from fastapi.exceptions import HTTPException
from pydantic import BaseModel

from app.shared.auth.token_handler import generate_confirmation_token, confirm_token
from app.shared.bases.base_model import ModelType, ModelMixin
from app.shared.middleware.json_encoders import ModelEncoder
from app.shared.schemas.ResponseSchemas import BaseResponse
from settings import Config
from fastapi.logger import logger, logging

JWT_SECRET = Config.fastapi_key
JWT_ALGORITHM = Config.jwt_algo
ADMIN_SECRET = Config.admin_key
AGENT_SECRET = Config.agent_key


logger.name = "AuthHandler"
logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.INFO)


def token_response(token_detail: Any) -> Any:
    """
    The token_response function returns a dictionary containing the token and refresh_token.
    The function takes in two parameters, token and refresh_token. The function returns a dictionary
    containing the token and refresh_token.

    :param token_detail: Used to Store the token that is returned by the oauth2 server.
    :return: A dictionary with the following keys: access_token
    """
    return Any(success=True, response=token_detail)


def generate_main_jwt(user_claim: Any, secret: str = JWT_SECRET) -> str:
    """
    The generate_main_jwt function generates a JWT token for the user.
    It takes in a refresh_token and returns an access_token. The access token is valid for 10 minutes.

    :param secret:
    :param user_claim: Used to Generate the access_token.
    :return: A jwt token that is generated from the refresh_token.

    """
    payload = user_claim.dict() | {
        "expires": time.time() + timedelta(minutes=10).seconds
    }

    return jwt.encode(
        payload, secret, algorithm=JWT_ALGORITHM, json_encoder=ModelEncoder
    )


def sign_jwt(claim: Any) -> Any:
    """
    takes a claim and returns a token
    """
    secret = JWT_SECRET
    if claim.admin:
        secret = ADMIN_SECRET
    if claim.agent:
        secret = AGENT_SECRET
    logger.info(f"signing jwt with secret {secret}")
    token = generate_main_jwt(claim, secret)
    return token_response(Any(access_token=token, user_claim=claim))


def decode_jwt(token: str, admin=False, agent=False) -> Any:
    """
    The decode_jwt function takes a token and checks if it is valid. If the token is valid,
    it returns the claims of that token. Otherwise, it returns None.

    :param agent: Used to Determine if the token is an agent token or a user token.
    :param token:str: Used to Pass in the token that is being decoded.
    :param admin: Used to Determine if the token is an admin token or a user token.
    :return: The decoded token as a dictionary.
    """

    def _get_user_type():
        for secret in [ADMIN_SECRET, AGENT_SECRET, JWT_SECRET]:
            with contextlib.suppress(jwt.exceptions.InvalidSignatureError):
                logger.info(f"trying secret {secret}")
                return jwt.decode(token, secret, algorithms=[JWT_ALGORITHM])

    # logger.info(f"decoded jwt with token {token}")

    if claim := _get_user_type():
        logger.info(f"decoded {token} with claim {claim}")
    return Any(**claim or None)
