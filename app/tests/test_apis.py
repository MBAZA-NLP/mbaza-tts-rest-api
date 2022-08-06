from http import HTTPStatus

import pytest
from app.core import config
from app.main import app
from fastapi.testclient import TestClient

client = TestClient(app)


@pytest.fixture()
def api_token():
    # Get token.
    res = client.post(
        "/token",
        headers={"Accept": "application/x-www-form-urlencoded"},
        data={
            "username": config.API_USERNAME,
            "password": config.API_PASSWORD,
        },
    )
    res_json = res.json()

    access_token = res_json["access_token"]
    token_type = res_json["token_type"]

    return f"{token_type} {access_token}"


def test_speak(api_token):
    # Unauthorized request.
    response = client.get("/speak/Hello")
    assert response.status_code == HTTPStatus.UNAUTHORIZED

    # Authorized but should raise 400 error.
    response = client.get(
        "/speak/",
        headers={
            "Accept": "application/json",
            "Authorization": api_token,
        },
    )
    assert response.status_code == HTTPStatus.NOT_FOUND

    # Successful request.
    response = client.get(
        "/speak/Hello",
        headers={
            "Accept": "application/json",
            "Authorization": api_token,
        },
    )
    assert response.status_code == HTTPStatus.OK
