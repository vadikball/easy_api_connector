"""Base schemas."""
from enum import StrEnum
from typing import Generic, TypeVar

from pydantic import BaseModel, Field

PageData = TypeVar("PageData")
OrderByEnumType = TypeVar("OrderByEnumType", bound=StrEnum)


class OrderDirectionEnum(StrEnum):
    ASC = "ASC"
    DESC = "DESC"


class PageParams(BaseModel):
    page: int = Field(default=1, ge=1)
    size: int = Field(default=10, ge=1)


class Page(PageParams, Generic[PageData]):
    total_pages: int
    page_data: PageData


class OrderParams(BaseModel, Generic[OrderByEnumType]):
    order_by: OrderByEnumType | None = None
    order_direction: OrderDirectionEnum | None = None
