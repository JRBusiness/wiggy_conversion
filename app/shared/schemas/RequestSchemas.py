"""
@author: Kuro
"""
from typing import Optional
from uuid import UUID

from fastapi_camelcase import CamelModel
from pydantic import BaseModel, validator


class BaseRequest(CamelModel):
    """
    Request factory for our abstract input class
    """

    primary_key: UUID
    optional_key: Optional[UUID]

    class Config:
        """
        Base Config Object with example
        """

        schema_extra = {
            "example": {
                "userId": "eb773795-b3a2-4d0e-af1d-4b1c9d90ae26",
            }
        }


class GetObjects(BaseRequest):
    """
    GetObjects represents a generic getter for a list of objects
    to be fetched from the database with a single common key.
    """

    pass


class CloseObject(BaseRequest):
    """
    CloseObject exists as an abstract input schema to mark
    and object inactive in the database.
    """

    pass


class GetAwaitable(BaseModel):
    """
    GetAwaitable exists as an abstract input schema to mark
    and object as active in the database.
    """

    @validator("HTTP_AUTHORIZATION")
    def validate_token(cls, v):
        if not v or "Bearer" not in v:
            raise ValueError("Token is required to use the format: Bearer <token>")
        return v

    HTTP_AUTHORIZATION: Optional[str]
