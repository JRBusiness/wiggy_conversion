from typing import Any, List, Optional, Union
from uuid import UUID

from pydantic import BaseModel
from redis_om import RedisModel


class BaseResponse(BaseModel):
    """
    Base Response abstraction for standardized returns
    """

    success: bool = False
    error: Optional[str] = None
    response: Optional[Any] = None

    class Config:
        arbitrary_types_allowed = True

    def dict(self, *args, **kwargs) -> dict[str, Any]:
        """
        Override the default dict method to exclude None values in the response
        """
        kwargs.pop("exclude_none", None)
        return super().dict(*args, exclude_none=True, **kwargs)


class PagedResponse(RedisModel):
    """
    PagedResponse is a response object that contains a list of objects and
    pagination information for the client to use.
    """

    items: List[Any]
    page: int
    page_size: int
    pages: int
    total: int


class PagedBaseResponse(BaseResponse):
    """
    PagedBaseResponse is a response object that
    contains a list of objects
    """

    response: Optional[PagedResponse]


class GetObjectsResponse(BaseResponse):
    """
    GetObjectsResponse is a response object that
    contains a list of objects
    """

    response: List[Any]


class GetObjectResponse(BaseResponse):
    """
    GetObjectResponse is a response object that
    contains a single item in the response body
    """

    response: Any


class CloseObjectsResponse(BaseResponse):
    """
    It's a response object that tells the client what to
    expect when calling the `CloseObject` method.
    """

    pass


class CreateObjectResponse(BaseResponse):
    """
    CreateObjectResponse creates a response object for the given API request.
    """

    pass
