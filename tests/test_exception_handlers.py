import fastapi
import fastapi.testclient

import app.core.exception_handlers
import app.core.exceptions
import app.core.middleware

# 独立小应用：只测异常处理，不依赖真实数据库。
error_application = fastapi.FastAPI()

# 两个注册缺一不可：中间件生成 request_id，异常处理器统一错误结构。
app.core.middleware.register_middlewares(error_application)
app.core.exception_handlers.register_exception_handlers(error_application)


@error_application.get("/business-error")
async def business_error():
    raise app.core.exceptions.ResourceNotFoundException(
        "Product does not exist.",
    )


@error_application.get("/http-error")
async def http_error():
    raise fastapi.HTTPException(
        status_code=403,
        detail="Permission denied.",
    )


@error_application.get("/validation-error")
async def validation_error(
    quantity: int,
):
    return {"quantity": quantity}


@error_application.get("/unexpected-error")
async def unexpected_error():
    raise RuntimeError("boom")


client = fastapi.testclient.TestClient(error_application)


# 业务异常
def test_business_exception():
    response = client.get("/business-error")

    assert response.status_code == 404
    body = response.json()
    assert body["error"]["code"] == "RESOURCE_NOT_FOUND"
    assert body["error"]["request_id"] == response.headers["X-Request-ID"]


# HTTP 异常
def test_http_exception():
    response = client.get("/http-error")

    assert response.status_code == 403
    body = response.json()
    assert body["error"]["code"] == "HTTP_ERROR"
    assert body["error"]["request_id"] == response.headers["X-Request-ID"]


# 参数校验异常
def test_validation_exception():
    response = client.get(
        "/validation-error",
        params={"quantity": "invalid"},
    )

    assert response.status_code == 422
    body = response.json()
    assert body["error"]["code"] == "VALIDATION_ERROR"
    assert isinstance(body["error"]["details"], list)
    assert body["error"]["request_id"] == response.headers["X-Request-ID"]


def test_request_id_is_preserved_from_header():
    response = client.get(
        "/business-error",
        headers={"X-Request-ID": "test-request-id-123"},
    )

    assert response.headers["X-Request-ID"] == "test-request-id-123"
    assert response.json()["error"]["request_id"] == "test-request-id-123"


def test_invalid_request_id_is_replaced():
    response = client.get(
        "/business-error",
        headers={"X-Request-ID": "bad value with spaces"},
    )

    assert response.status_code == 404
    assert response.headers["X-Request-ID"] != "bad value with spaces"


def test_unexpected_exception():
    safe_client = fastapi.testclient.TestClient(
        error_application,
        raise_server_exceptions=False,
    )

    response = safe_client.get("/unexpected-error")

    assert response.status_code == 500
    body = response.json()
    assert body["error"]["code"] == "INTERNAL_SERVER_ERROR"
    assert body["error"]["request_id"] == response.headers["X-Request-ID"]