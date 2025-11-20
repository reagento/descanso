import asyncio
import concurrent.futures
from threading import Thread

import pytest

from .server import new_site


class MyRunner:
    loop: asyncio.AbstractEventLoop
    future: asyncio.Future

    def __init__(self, port: int) -> None:
        self.port = port
        self.ready = concurrent.futures.Future()

    async def arun(self):
        self.loop = asyncio.get_event_loop()
        self.future = self.loop.create_future()
        site = await new_site(8080)
        await site.start()
        self.ready.set_result(True)
        await self.future
        await site.stop()

    def run(self):
        asyncio.run(self.arun())

    def stop(self):
        self.loop.call_soon_threadsafe(self.future.set_result, None)


@pytest.fixture(scope="module")
def server_addr():
    runner = MyRunner(8080)
    t = Thread(target=runner.run)
    t.start()
    runner.ready.result()
    yield "http://127.0.0.1:8080"
    runner.stop()
    t.join()
