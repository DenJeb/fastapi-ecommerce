import fastapi
import fastapi.testclient

import app.core.exception_handlers
import app.core.exceptions

test_application = fastapi.FastAPI()
test_application.__test__ = False

app.core.exception_handlers.register_exception_handlers(
    test_application,
)


@test_application.get("/business-error")
async def business_error():
    raise app.core.exceptions.ResourceNotFoundException(
        "Product does not exist.",
    )


@test_application.get("/http-error")
async def http_error():
    raise fastapi.HTTPException(
        status_code=403,
        detail="Permission denied.",
    )


@test_application.get("/validation-error")
async def validation_error(
    quantity: int,
):
    return {"quantity": quantity}


client = fastapi.testclient.TestClient(test_application)


# 业务异常
def test_business_exception():
    response = client.get("/business-error")

    assert response.status_code == 404
    assert response.json()["code"] == "RESOURCE_NOT_FOUND"


# HTTP 异常
def test_http_exception():
    response = client.get("/http-error")

    assert response.status_code == 403
    assert response.json()["code"] == "HTTP_ERROR"


# 参数校验异常
def test_validation_exception():
    response = client.get(
        "/validation-error",
        params={"quantity": "invalid"},
    )

    assert response.status_code == 422
    assert response.json()["code"] == "VALIDATION_ERROR"
