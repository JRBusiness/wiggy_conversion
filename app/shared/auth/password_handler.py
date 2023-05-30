"""
@author: Kuro
"""
from typing import Union

from passlib.context import CryptContext


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    It takes a plain text password and a hashed password and returns True if the plain text password matches the hashed password

    :param plain_password: The password that the user entered
    :type plain_password: str
    :param hashed_password: The hashed password that you want to verify
    :type hashed_password: str
    :return: A boolean value.
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    It takes a string and returns a string

    :param password: The password to hash
    :type password: str
    :return: A string
    """
    return pwd_context.hash(password, rounds=12)


"""
@author: Kuro
"""
import hashlib
from typing import Union

from passlib.context import CryptContext

#
# pwd_context = CryptContext(schemes=["hex_md5"])
# md5_key = "89b5b987124d2ec3"
#
# def verify_password(plain_password: str, hashed_password: str) -> bool:
#     """
#     It takes a plain text password and a hashed password and returns True
#     if the plain text password matches the hashed password
#
#     :param plain_password: The password that the user entered
#     :type plain_password: str
#     :param hashed_password: The hashed password that you want to verify
#     :type hashed_password: str
#     :return: A boolean value.
#     """
#     password_context = plain_password + md5_key
#     md5_sign = hashlib.md5(password_context.encode()).hexdigest()
#     return pwd_context.verify(md5_sign, hashed_password)
#
#
# def get_password_hash(password: str) -> str:
#     """
#     It takes a string and returns a string
#
#     :param password: The password to hash
#     :type password: str
#     :return: A string
#     """
#     password_context = password + md5_key
#     md5_sign = hashlib.md5(password_context.encode()).hexdigest()
#     return pwd_context.hash(md5_sign)
#
