"""tests for checking automaticially created api routes
"""

import os
from fastapi.testclient import TestClient


from apifactory.app_factory import ApiFactory


BASE_PATH = os.path.abspath(os.path.dirname(__file__))

file_name = os.path.join(BASE_PATH, "testfiles/test.yaml")
app = ApiFactory.from_yaml(file_name).app_factory()


client = TestClient(app)


def test_login():
    """[summary]"""
    response = client.post(
        "/login",
        headers={
            "accept": "application/json",
            "Content-Type": "application/x-www-form-urlencoded",
        },
    )
    assert response.status_code == 422
    response = client.post(
        "/login",
        headers={
            "accept": "application/json",
            "Content-Type": "application/x-www-form-urlencoded",
        },
        data="grant_type=&username=admin&password=admin&scope=&client_id=&client_secret=",
    )
    assert response.status_code == 200


bearer_token = client.post(
    "/login",
    headers={
        "accept": "application/json",
        "Content-Type": "application/x-www-form-urlencoded",
    },
    data="grant_type=&username=admin&password=admin&scope=&client_id=&client_secret=",
)
bearer_token = bearer_token.json()
token = bearer_token["access_token"]
bearer = bearer_token["token_type"]


header = {"accept": "application/json", "Authorization": f"{bearer} {token}"}


def test_get_all():
    response = client.get("test_table/", headers=header)
    assert response.status_code == 200


def test_params():
    response = client.get("test_table/?limit=100&primarykey=0", headers=header)
    assert response.status_code == 200
    response = client.get("test_table/?limit=100&invalidparam=0", headers=header)
    assert response.status_code == 400


def test_get_id():
    response = client.get("test_table/0", headers=header)
    assert response.status_code == 200
    response = client.get("test_table/1", headers=header)
    assert response.status_code == 404


def test_post():
    ...


def test_put():
    ...


def test_delete():
    ...
