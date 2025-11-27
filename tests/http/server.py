from aiohttp import web


async def query_xxy(request: web.Request) -> web.Response:
    assert request.query_string == "x=1&x=2&y=3"
    return web.Response(text="ok")


async def conflict(request: web.Request) -> web.Response:
    return web.Response(
        status=409,
        reason="test_conflict",
        body="test_conflict_body",
    )


async def headers(request: web.Request) -> web.Response:
    assert request.headers["X-Test"] == "1"
    return web.Response(
        headers=[
            ("X-Test", "2"),
            ("X-Test", "3"),
            ("Another", "value"),
        ],
    )


async def delete(request: web.Request) -> web.Response:
    return web.Response(status=204)


async def files(request: web.Request) -> web.Response:
    data = await request.post()
    f1: web.FileField = data["x1"]
    assert f1.filename == "x1"
    assert f1.file.read() == b"1"

    f2: web.FileField = data["x2"]
    assert f2.filename == "x2"
    assert f2.file.read() == b"2"

    f3: web.FileField = data["x3"]
    assert f3.filename == "z3"
    assert f3.content_type == "test_content_type"
    assert f3.file.read() == b"3"
    return web.Response()


async def form(request: web.Request) -> web.Response:
    data = await request.post()
    assert data["field1"] == "1"
    assert data["field2"] == "2"
    return web.Response()


async def json(request: web.Request) -> web.Response:
    data = await request.json()
    assert data == {"x": 1}
    return web.json_response({"y": 2})


async def jsonrpc(request: web.Request) -> web.Response:
    data = await request.json()
    request_id = data["id"]
    assert data["jsonrpc"] == "2.0"
    if data["method"] == "good":
        assert data["params"] == [42]
        return web.json_response(
            {
                "id": request_id,
                "jsonrpc": "2.0",
                "result": 42,
            },
        )
    elif data["method"] == "bad":
        return web.json_response(
            {
                "id": request_id,
                "jsonrpc": "2.0",
                "error": {
                    "code": -32000,
                    "message": "My error",
                },
            },
        )
    else:
        return web.json_response(
            {
                "id": request_id,
                "jsonrpc": "2.0",
                "error": {
                    "code": -32601,
                    "message": "Method not found",
                },
            },
        )


def new_app() -> web.Application:
    app = web.Application()
    app.add_routes(
        [
            web.get("/query_xxy", query_xxy),
            web.get("/conflict", conflict),
            web.get("/headers", headers),
            web.get("/json", json),
            web.delete("/delete", delete),
            web.post("/files", files),
            web.post("/form", form),
            web.post("/jsonrpc", jsonrpc),
        ],
    )
    return app


async def new_site(port: int) -> web.TCPSite:
    app = new_app()
    app_runner = web.AppRunner(app)
    await app_runner.setup()
    return web.TCPSite(app_runner, "localhost", port)
