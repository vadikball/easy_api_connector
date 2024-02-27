"""Base connector."""

from enum import StrEnum
from typing import Any

import httpx

from easy_api_connector.descriptors import ProxyDesc
from easy_api_connector.enums import Methods

params_type = dict[str, str | int] | None  # noqa: WPS465


class Method:
    _endpoint: StrEnum
    _method: Methods

    def __init__(self, connector: "BaseConnector"):
        self._connector = connector

    async def __call__(
        self,
        payload: dict | None = None,
        identity: Any = None,
        r_params: params_type = None,
        secondary: str | None = None,
        secondary_identity: Any = None,
    ) -> httpx.Response:
        return await self._connector.send_request(
            endpoint=self._endpoint,
            method=self._method,
            payload=payload,
            identity=identity,
            r_params=r_params,
            secondary=secondary,
            secondary_identity=secondary_identity,
        )


def method_factory(endpoint: str, method: StrEnum) -> type[Method]:
    class ConcreteMethod(Method):
        _endpoint = endpoint
        _method = method

    return ConcreteMethod


class Endpoint:
    _endpoint: StrEnum
    get: Method
    post: Method
    put: Method
    delete: Method

    def __init__(self, connector: "BaseConnector"):
        self._connector = connector

    async def __call__(
        self,
        method: Methods = Methods.get,
        payload: dict | None = None,
        identity: Any = None,
        r_params: params_type = None,
        secondary: str | None = None,
        secondary_identity: Any = None,
    ) -> httpx.Response:
        return await self._connector.send_request(
            endpoint=self._endpoint,
            method=method,
            payload=payload,
            identity=identity,
            r_params=r_params,
            secondary=secondary,
            secondary_identity=secondary_identity,
        )


MethodProxyDesc = ProxyDesc[Method, Endpoint]


def endpoint_factory(endpoint: str, methods: type[StrEnum] = Methods) -> type[Endpoint]:
    class ConcreteEndpoint(Endpoint):
        _endpoint = endpoint

    method: StrEnum
    for method in methods:
        setattr(
            ConcreteEndpoint, method.name, MethodProxyDesc(
                method_factory(endpoint, method), attr_name="_connector"
            )
        )

    return ConcreteEndpoint


class BaseConnector:
    __url__: str

    def __init__(
        self, client: httpx.AsyncClient
    ):
        self._client = client

    async def send_request(
        self,
        endpoint: StrEnum,
        method: Methods = Methods.get,
        payload: dict | None = None,
        identity: Any = None,
        r_params: params_type = None,
        secondary: str | None = None,
        secondary_identity: Any = None,
    ) -> httpx.Response:
        url = self._build_url(endpoint, identity, secondary, secondary_identity)

        request = self._client.build_request(
            str(method.value),
            url,
            json=payload,
            params=r_params,
        )

        response = await self._client.send(request)

        if not response.is_success:
            raise httpx.HTTPStatusError(
                "{0} {1}".format(str(response.status_code), response.content.decode()),
                request=request,
                response=response,
            )

        return response

    def _build_url(
        self,
        endpoint: StrEnum,
        identity: Any,
        secondary: str | None,
        secondary_identity: Any,
    ) -> str:
        url = self.__url__ + endpoint  # type: ignore

        if identity:
            url = "{0}/{1}".format(url, str(identity))

        if secondary:
            url = "{0}/{1}".format(url, secondary)
            if secondary_identity:
                url = "{0}/{1}".format(url, str(secondary_identity))

        return url


EndpointProxyDesc = ProxyDesc[Endpoint, BaseConnector]


def base_connector_class_factory(
    endpoints: type[StrEnum], base_url: str, methods: type[StrEnum] = Methods
) -> type[BaseConnector]:
    class Connector(BaseConnector):
        __url__ = base_url

    for endpoint in endpoints:
        setattr(Connector, endpoint, EndpointProxyDesc(endpoint_factory(endpoint, methods), attr_name=None))

    return Connector
