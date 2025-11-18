from io import BytesIO

import pytest
import pytest_asyncio
from aiohttp import ClientSession, web

from descanso import RestBuilder
from descanso.http.aiohttp import AiohttpClient
from descanso.request_transformers import File


async def hello(request: web.Request) -> web.Response:
    data = await request.post()
    f1: web.FileField = data["f1"]
    assert f1.filename == "f1"
    assert f1.file.read() == b"1"

    f2: web.FileField = data["x2"]
    assert f2.filename == "x2"
    assert f2.file.read() == b"2"

    f3: web.FileField = data["x3"]
    assert f3.filename == "z"
    assert f3.file.read() == b"3"

    f4: web.FileField = data["x4"]
    assert f4.filename == "z"
    assert f4.content_type == "other"
    assert f4.file.read() == b"4"
    return web.Response(text="[42]")


@pytest_asyncio.fixture
async def server():
    app = web.Application()
    app.add_routes([web.post("/", hello)])
    app_runner = web.AppRunner(app)
    await app_runner.setup()
    site = web.TCPSite(app_runner, "localhost", 8080)
    await site.start()
    yield app_runner
    await app_runner.cleanup()


@pytest.mark.asyncio
async def test_simple(server):
    rest = RestBuilder()
    class Api(AiohttpClient):
        @rest.post(
            "/",
           File("f1"),
           File("f2", filefield="x2"),
           File("f3", filefield="x3", filename="z"),
           File("f4", filefield="x4", filename="z", content_type="other"),
        )
        async def send(self, f1, f2, f3, f4) -> list[int]:
            raise NotImplementedError

    x1 = BytesIO(b"1")
    x2 = BytesIO(b"2")
    x3 = BytesIO(b"3")
    x4 = BytesIO(b"4")

    async with ClientSession() as session:
        client = Api(base_url="http://127.0.0.1:8080", session=session)
        assert await client.send(x1, x2, x3, x4) == [42]
