"""
@author: Kuro
"""
from itsdangerous import URLSafeTimedSerializer
from settings import Config
from fastapi.logger import logger


def generate_confirmation_token(data: str):
    serializer = URLSafeTimedSerializer(Config.fastapi_key)
    return serializer.dumps(data, salt=Config.salt)


def confirm_token(token, expiration=30):
    serializer = URLSafeTimedSerializer(Config.fastapi_key)
    try:
        data = serializer.loads(token, salt=Config.salt, max_age=expiration)
    except Exception as e:
        logger.info(e)
        return False
    return data
