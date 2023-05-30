"""
@author: Kuro
"""
from typing import Optional, Union, Any

from app.shared.schemas.ResponseSchemas import BaseResponse


class SafeException(BaseResponse):
    """
    Exception class for handling and sanitizing exceptions that occur during
    various operations such as loading and saving models, searches, and other operations.
    """

    pass
