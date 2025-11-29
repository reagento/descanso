from contextlib import AbstractContextManager
from unittest.mock import Mock

from dirty_equals import DirtyEquals, HasAttributes, IsInstance

from descanso.client import SyncClient, SyncResponseWrapper
from descanso.request import HttpRequest


class _Dirty:
    def __getitem__(self, item: type):
        def check(**attrs) -> DirtyEquals:
            if not attrs:
                return IsInstance(item)
            return IsInstance(item) & HasAttributes(**attrs)

        return check


dirty = _Dirty()


class MockClient(SyncClient):
    def __init__(self, mock: Mock) -> None:
        self._mock = mock

    def send_request(
        self,
        request: HttpRequest,
    ) -> AbstractContextManager[SyncResponseWrapper]:
        return self._mock(request)
