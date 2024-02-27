"""Common connector implementation."""
from typing import Generic, TypeVar

from pydantic import BaseModel

from easy_api_connector.base_connector import BaseConnector, Endpoint
from easy_api_connector.descriptors import ProxyDesc as _ProxyDesc, SecondaryProxyDesc as _SecondaryProxyDesc
from easy_api_connector.schemas import Page


class ABCApi:
    def __init__(self, connector: BaseConnector):
        self.connector = connector


class BaseApi(ABCApi):
    connector: BaseConnector
    endpoint: str

    @property
    def _endpoint(self) -> Endpoint:
        return getattr(self.connector, self.endpoint)


class SecondaryBaseApi(BaseApi):
    secondary_endpoint: str


ListSchema = TypeVar("ListSchema")
InnerListSchema = TypeVar("InnerListSchema")
ListParams = TypeVar("ListParams")


class ListHandler(BaseApi, Generic[ListSchema, InnerListSchema, ListParams]):
    list_schema: type[ListSchema]
    inner_list_schema: type[InnerListSchema]
    list_params: type[ListParams]

    async def list(self, r_params: ListParams) -> ListSchema:
        if r_params is None:
            r_params = (
                self.list_params() if issubclass(self.list_params, BaseModel) else None
            )

        response = await self._endpoint.get(
            r_params=r_params.model_dump(exclude_unset=True) if r_params is not None else None  # type: ignore
        )
        if issubclass(self.list_schema, Page):
            return self.list_schema.model_validate(response.json())  # type: ignore

        assert issubclass(self.inner_list_schema, BaseModel)

        return [self.inner_list_schema.model_validate(entity) for entity in response.json()]  # type: ignore


class SecondaryListHandler(SecondaryBaseApi, Generic[ListSchema, InnerListSchema, ListParams]):
    list_schema: type[ListSchema]
    inner_list_schema: type[InnerListSchema]
    list_params: type[ListParams]

    async def list(self, r_params: ListParams) -> ListSchema:
        if r_params is None:
            r_params = (
                self.list_params() if issubclass(self.list_params, BaseModel) else None
            )

        response = await self._endpoint.get(
            r_params=r_params.model_dump(exclude_unset=True) if r_params is not None else None,  # type: ignore
            secondary=self.secondary_endpoint,
        )
        if issubclass(self.list_schema, Page):
            return self.list_schema.model_validate(response.json())  # type: ignore

        assert issubclass(self.inner_list_schema, BaseModel)

        return [self.inner_list_schema.model_validate(entity) for entity in response.json()]  # type: ignore


IdentityType = TypeVar("IdentityType")
SecondaryIdentityType = TypeVar("SecondaryIdentityType")
DetailSchema = TypeVar("DetailSchema", bound=BaseModel)


class DetailHandler(BaseApi, Generic[IdentityType, DetailSchema]):
    detail_schema: type[DetailSchema]

    async def detail(self, identity: IdentityType) -> DetailSchema:
        response = await self._endpoint.get(identity=identity)
        return self.detail_schema.model_validate(response.json())


class DeleteHandler(BaseApi, Generic[IdentityType]):
    async def delete(self, identity: IdentityType) -> None:
        await self._endpoint.delete(identity=identity)


class SecondaryDeleteHandler(SecondaryBaseApi, Generic[IdentityType, SecondaryIdentityType]):
    async def delete(self, identity: IdentityType, secondary_identity: SecondaryIdentityType) -> None:
        await self._endpoint.delete(
            identity=identity, secondary=self.secondary_endpoint, secondary_identity=secondary_identity
        )


PutSchema = TypeVar("PutSchema", bound=BaseModel)


class PutHandler(BaseApi, Generic[IdentityType, PutSchema]):
    put_schema: type[PutSchema]

    async def put(self, body: PutSchema, identity: IdentityType) -> None:
        await self._endpoint.put(
            payload=body.model_dump(exclude_unset=True, mode="json"), identity=identity
        )


PostSchema = TypeVar("PostSchema", bound=BaseModel)
PostResponse = TypeVar("PostResponse", bound=BaseModel)


class PostHandler(BaseApi, Generic[PostSchema, PostResponse]):
    post_schema: type[PostSchema]
    post_response: type[PostResponse]

    async def post(self, body: PostSchema) -> PostResponse:
        response = await self._endpoint.post(payload=body.model_dump(exclude_unset=True, mode="json"))
        return self.post_response.model_validate(response.json())


class SecondaryPostHandler(SecondaryBaseApi, Generic[PostSchema]):
    post_schema: type[PostSchema]

    async def post(self, body: PostSchema) -> None:
        await self._endpoint.post(
            payload=body.model_dump(exclude_unset=True, mode="json"), secondary=self.secondary_endpoint
        )


ProxyDesc = _ProxyDesc[BaseApi, ABCApi]
SecondaryProxyDesc = _SecondaryProxyDesc[SecondaryBaseApi, BaseApi]
