"""tests for checking automaticially created api routes
"""

import os
from fastapi.testclient import TestClient
import pytest

from apifactory.app_factory import ApiFactory


BASE_PATH = os.path.abspath(os.path.dirname(__file__))

file_name = os.path.join(BASE_PATH, "testfiles/test.yaml")
app = ApiFactory.from_yaml(file_name).app_factory()


client = TestClient(app)

HEADER = {
    "accept": "application/json",
    "Content-Type": "application/x-www-form-urlencoded",
}

LOGIN_PARAMS = [
    (None, 422),
    ("grant_type=&username=admin&password=admin&scope=&client_id=&client_secret=", 200),
    (
        "grant_type=&username=mcdoesntexist&password=admin&scope=&client_id=&client_secret=",
        404,
    ),
    ("grant_type=&username=admin&password=wrong&scope=&client_id=&client_secret=", 404),
]


@pytest.mark.parametrize("data,expected_response", LOGIN_PARAMS)
def test_login(data, expected_response):
    """[summary]"""
    response = client.post("/login", headers=HEADER, data=data)
    assert response.status_code == expected_response


bearer_token = client.post(
    "/login",
    headers=HEADER,
    data="grant_type=&username=admin&password=admin&scope=&client_id=&client_secret=",
)
bearer_token = bearer_token.json()
token = bearer_token["access_token"]
bearer = bearer_token["token_type"]


header = {"accept": "application/json", "Authorization": f"{bearer} {token}"}


def test_get_all():
    response = client.get("test_table/", headers=header)
    assert response.status_code == 200


PARAMS = [
    ("test_table/?limit=100&primarykey=0", 200),
    ("test_table/?limit=100&invalidparam=0", 400),
]


@pytest.mark.parametrize("url,expected_response", PARAMS)
def test_params(url, expected_response):
    response = client.get(url, headers=header)
    assert response.status_code == expected_response


GET_IDS = [("test_table/0", 200), ("test_table/1", 404)]


@pytest.mark.parametrize("url,expected_response", GET_IDS)
def test_get_id(url, expected_response):
    response = client.get(url, headers=header)
    assert response.status_code == expected_response


def test_post():
    data = {"primarykey": 2, "someothercoll": "test"}
    response = client.post("test_table/", headers=header, json=data)
    assert response.status_code == 200
    # check if inserted in db
    response = client.get("test_table/2", headers=header)
    assert response.status_code == 200


def test_bulk_post():
    """test bulk insert"""
    data = [
        {"primarykey": 3, "someothercoll": "test"},
        {"primarykey": 4, "someothercoll": "test"},
    ]
    response = client.post("test_table/", headers=header, json=data)
    assert response.status_code == 200
    # check if inserted in db
    response = client.get("test_table/3", headers=header)
    assert response.status_code == 200
    response = client.get("test_table/4", headers=header)
    assert response.status_code == 200


UPDATES = [("test_table/2", 200), ("test_table/9000", 404)]


@pytest.mark.parametrize("url,expected_response", UPDATES)
def test_put(url, expected_response):
    data = {"primarykey": 2, "someothercoll": "someother"}
    response = client.put(url, headers=header, json=data)
    assert response.status_code == expected_response
    if expected_response == 200:
        response = client.get(url, headers=header)
        assert response.json()["someothercoll"] == "someother"


UPDATES = [
    (
        ["test_table/2", "test_table/3"],
        [
            {"primarykey": 2, "someothercoll": "someother"},
            {"primarykey": 3, "someothercoll": "someother"},
        ],
        200,
    )
]


@pytest.mark.parametrize("urls,data,expected_response", UPDATES)
def test_put_many(urls, data, expected_response):
    response = client.put("test_table/", headers=header, json=data)
    assert response.status_code == expected_response
    if expected_response == 200:
        for url in urls:
            response = client.get(url, headers=header)
            assert response.json()["someothercoll"] == "someother"


DELETES = [("test_table/2", 200), ("test_table/9000", 404)]


@pytest.mark.parametrize("url,expected_response", DELETES)
def test_delete(url, expected_response):
    response = client.delete(url, headers=header)
    assert response.status_code == expected_response
    if expected_response == 200:
        response = client.get(url, headers=header)
        assert response.status_code == 404


DELETE = [("test_table/", [{"primarykey": 3}, {"primarykey": 4}], 200)]


@pytest.mark.parametrize("url,data,expected_response", DELETE)
def test_delete_multiple(url, data, expected_response):
    response = client.delete(url, json=data, headers=header)
    assert response.status_code == expected_response
