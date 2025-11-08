import logging
import os
from dataclasses import dataclass
from enum import Enum
from typing import Generic, TypeVar

from adaptix import Chain, Retort, dumper
from requests import Session

from descanso import get
from descanso.http.requests import RequestsClient
from descanso.request_transformers import Query

T = TypeVar("T")


@dataclass
class Response(Generic[T]):
    response: T


@dataclass
class User:
    id: int
    first_name: str
    last_name: str


class GenderQuery(Enum):
    MALE = 2
    FEMALE = 1
    ANY = 9


@dataclass
class UsersSearchResult:
    count: int
    items: list[User]


class VkClient(RequestsClient):
    def __init__(self, token: str):
        self.token = token
        query_dumper = Retort(recipe=[
            dumper(bool, int),
            dumper(int, str),
            dumper(list[int], lambda d: ",".join(d), Chain.LAST),
            dumper(list[str], lambda d: ",".join(d), Chain.LAST),
        ])
        body_retort = Retort()
        super(VkClient, self).__init__(
            base_url="https://api.vk.com/method/",
            session=Session(),
            transformers=[
                Query("access_token", "{self.token}"),
                Query("v", "5.131"),
            ],
            request_params_dumper=query_dumper,
            request_body_dumper=body_retort,
            response_body_loader=body_retort,
        )

    def set_token(self, token: str) -> None:
        self.token = token

    @get("users.get")
    def get_users(self, user_ids: list[str]) -> Response[list[User]]:
        """Get users by their ids"""

    @get("users.search")
    def search_users(
            self, q: str, sort: bool = False,
            offset: int = 0, count: int = 20,
            gender: GenderQuery = GenderQuery.ANY,
    ) -> Response[UsersSearchResult]:
        """Search users with pagination"""


TOKEN = os.getenv("VK_TOKEN")


def main():
    logging.basicConfig(level=logging.INFO)
    client = VkClient(TOKEN)
    print(client.get_users(["1", "2"]))
    print(client.search_users(q="tishka17", gender=GenderQuery.MALE))


if __name__ == "__main__":
    main()
