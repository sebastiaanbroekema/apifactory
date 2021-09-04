"""testing ratelimiter
"""
import os
from fastapi.testclient import TestClient

from apifactory.app_factory import ApiFactory


BASE_PATH = os.path.abspath(os.path.dirname(__file__))

file_name = os.path.join(BASE_PATH, "testfiles/test_ratelimit.yaml")
app = ApiFactory.from_yaml(file_name).app_factory()


client = TestClient(app)

HEADER = {
    "accept": "application/json",
    "Content-Type": "application/x-www-form-urlencoded",
}

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
    response = client.get("test_table/", headers=header)
    assert response.status_code == 429
