from typing import Any, Generic, TypeVar


ProxyType = TypeVar("ProxyType")
InstanceType = TypeVar("InstanceType")


class ProxyDesc(Generic[ProxyType, InstanceType]):
    def __init__(self, proxy: type[ProxyType], attr_name: str | None = "connector"):
        self.proxy = proxy
        self.attr_name = attr_name

    def __get__(self, instance: InstanceType, owner: Any) -> ProxyType:
        """Descriptor to get initialized instance of api connector."""
        if self.attr_name is None:
            return self.proxy(instance)

        return self.proxy(getattr(instance, self.attr_name))


class SecondaryProxyDesc(Generic[ProxyType, InstanceType]):
    def __init__(self, proxy_api: type[ProxyType]):
        self.proxy = proxy_api

    def __get__(self, instance: InstanceType, owner: Any) -> ProxyType:
        """Descriptor to get initialized instance of secondary api connector."""
        endpoint = getattr(self.proxy, "endpoint", None)
        if endpoint is None:
            self.proxy.endpoint = instance.endpoint

        self.__get__ = self.get_after_endpoint_set
        return self.proxy(instance.connector)

    def get_after_endpoint_set(self, instance: ProxyType, owner: Any) -> ProxyType:
        """Descriptor to get initialized instance of secondary api connector after singed endpoint."""

        return self.proxy(instance.connector)
