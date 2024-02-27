"""Connector enums."""
import enum


class Methods(enum.StrEnum):
    get = "GET"
    post = "POST"
    put = "PUT"
    delete = "DELETE"
