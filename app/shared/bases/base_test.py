"""
@author: Kuro
"""
from fastapi.testclient import TestClient

from app import app
from app.api.admin.schema import BaseUser

# from app.api.post.schema import GetPagedPost
from app.endpoints.routes import add_routes
from app.shared.auth.auth_handler import sign_jwt

user_data = {
    "id": "eb773795-b3a2-4d0e-af1d-4b1c9d90ae26",
    "username": "jory",
    "phone": "+14062093508",
    "name": "Jory",
    "birthdate": "1978-03-22",
    "created": "2021-11-18 22:09:05.842894",
}

test_user = BaseUser(**user_data)
user_id = str(test_user.id)
access_token = sign_jwt(user_id)
auth_header = {"Authorization": "Bearer 1337H4X"}
client = TestClient(app)
add_routes()


def mock_post(url, data):
    response = client.post(url, headers=auth_header, json=data)
    readout(response)
    assert response.status_code == 200
    return response


def readout(response):
    print("\n----------------RESPONSE READOUT----------------")
    print("status_code: ", response.status_code)
    print("json: ", response.json())
    print("--------------------------------------------")
