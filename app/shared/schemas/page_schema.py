"""
@author: Kuro
"""
from fastapi.types import Any
from fastapi_camelcase import CamelModel
from typing import List, Optional, Dict
from uuid import UUID

from app.shared.schemas.orm_schema import ORMCamelModel


class Params(CamelModel):
    page: int
    size: int

    class Config:
        schema_extra = {"example": {"page": "1", "size": "10"}}


class Filter(CamelModel):
    filter: Optional[Dict[str, UUID]]


class Post(CamelModel):
    post_id: UUID


class GetOptionalContextPages(CamelModel):
    context: Optional[Filter]
    params: Params


class GetNoContextPages(CamelModel):
    params: Params


class GetPages(CamelModel):
    context: Filter
    params: Params


class GetCommentPages(CamelModel):
    context: Post
    params: Params


class PagedResponse(ORMCamelModel):
    items: List[Any]
    page: int
    page_size: int
    pages: int
    total: int
