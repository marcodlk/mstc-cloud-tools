import os

import pytest
from flask import request

from .apps.hostname.app import create_hostname_app

SCRATCH_DIR = os.path.join(os.path.dirname(__file__), "scratch")
if not os.path.exists(SCRATCH_DIR):
    os.makedirs(SCRATCH_DIR)

@pytest.fixture()
def cleanup(request):
    def after():
        if request.session.testsfailed == 0:
            import shutil

            shutil.rmtree(SCRATCH_DIR)
            print("Removed " + SCRATCH_DIR)

    request.addfinalizer(after)

@pytest.fixture
def client():
    app = create_hostname_app(scratch_dir=SCRATCH_DIR)
    with app.app_context():
        return app.test_client()


def test_home(client):
    resp = client.get("/")
    print(str(resp.data))
    assert resp.status_code == 200
    assert len(resp.data.decode("utf8")) > 0


# TODO: currently failing with "address already in use" error

# def test_bad_input(client):
#     resp = client.post("/exec")
#     print("result: " + str(resp.status_code))
#     assert resp.status_code == 400


# def test_not_json(client):
#     resp = client.post("/exec", data="not json")
#     print("result: " + str(resp.status_code))
#     assert resp.status_code == 400


# def test_bad_json(client):
#     resp = client.post("/exec", json={"key": "value"})
#     print("result: " + str(resp.status_code))
#     assert resp.status_code == 400


# def test_json(client, cleanup):
#     import os
#     import json

#     import requests
#     from pytest_check import is_not_none

#     input = []
#     resp = client.post("/exec", json=input)
#     print(str(resp))
#     print("result: " + str(resp.status_code))
#     assert resp.status_code == 200
#     assert resp.content_type == "application/json"
#     response = resp.data.decode("utf8")
#     output_json = json.loads(response)
#     result_urls = output_json["outputs"]
#     is_not_none(result_urls)
#     for u in result_urls:
#         r = requests.get(u)
#         assert r.status_code == 200