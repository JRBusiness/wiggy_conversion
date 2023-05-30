"""
@author: Kuro
"""
from typing import Optional, List, Union, Any
from uuid import UUID

from app.shared.schemas.orm_schema import ORMCamelModel
from app.shared.schemas.page_schema import PagedResponse


class BaseResponse(ORMCamelModel):
    """
    Base Response abstraction for standardized returns
    """

    success: bool = False
    error: Optional[str]
    response: Optional[Optional[Union[str, dict, List[dict], UUID]]]

    class Config:
        arbitrary_types_allowed = True

    def dict(self, *args, **kwargs) -> dict[str, Any]:
        """
        Override the default dict method to exclude None values in the response
        """
        kwargs.pop("exclude_none", None)
        return super().dict(*args, exclude_none=True, **kwargs)


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
