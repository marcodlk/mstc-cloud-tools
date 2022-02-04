import os
from pathlib import Path

import pytest

from mstc_cloud_tools.client import Client, inside_cluster

NAME = "astros"
NAMESPACE = "mstc-dev"

ROUTE = "mstc/astros/exec"
ASTROS_REST = "localhost:31001"
ASTROS_DATA = "localhost:31002"


@pytest.fixture
def input():
    return [
        os.path.join(os.path.dirname(__file__), "data", "AstrosModalAGARD445.dat"),
        os.path.join(os.path.dirname(__file__), "data", "AstrosModalAGARD445.bdf"),
    ]


@pytest.fixture
def client():
    if inside_cluster():
        return Client(
            server="mstc-astros-service:8080/",
            route=ROUTE
        )
    else:
        return Client(
            server=ASTROS_REST,
            route=ROUTE,
            data_service=ASTROS_DATA
        )


@pytest.fixture(scope="session")
def service():
    import subprocess

    path = Path(os.path.dirname(__file__))
    get_cmd = ["kubectl", "get", "pods", "-n", NAMESPACE]
    pod_status = "Not Found"
    attempts = 0
    while attempts < 5:
        import time

        get_pods = subprocess.Popen(get_cmd, cwd=path, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        pod_list = get_pods.stdout.read().decode("utf-8")
        for line in pod_list.split("\n"):
            if NAME in line:
                parts = line.split()
                pod_status = parts[2]
                break
        if not ("Running" == pod_status):
            time.sleep(1)
            attempts += 1
            print("Retry attempt: " + str(attempts))
        else:
            break

    assert "Running" == pod_status, "Expected Running status, got: " + pod_status

    astros_version = "12.5"
    eap_version = "0.2.0"

    image = "mstc/" + NAME + "-" + astros_version + ":" + eap_version

    get_deployments_cmd = [
        "kubectl",
        "get",
        "deployments",
        "-o",
        "wide",
        "-n",
        NAMESPACE,
    ]
    get_deployments = subprocess.Popen(get_deployments_cmd, cwd=path, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    deployments_list = get_deployments.stdout.read().decode("utf-8")
    image_deployed = ""
    for line in deployments_list.split("\n"):
        if NAME in line:
            parts = line.split()
            image_deployed = parts[6]
            break
    assert image_deployed == image, "Expected " + image + " to be deployed, found: " + image_deployed

    yield

    # Shut it down at the end of the pytest session
    if os.environ.get("SKIP") is None:
        uninstall_cmd = ["helm", "uninstall", NAME, "--namespace", NAMESPACE]
        delete = subprocess.Popen(uninstall_cmd, cwd=path, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        print("\n" + delete.stdout.read().decode("utf-8"))


def test_client(client, input, service):
    import pytest_check

    #astros = Client(
    #    server=ASTROS_REST,
    #    route=ROUTE,
    #    data_service=ASTROS_DATA
    #)
    result = client.exec(input)
    pytest_check.is_not_none(result)
    pytest_check.is_true(result.startswith("http"))


def test_client_with_output_dir(client, input):
    import pytest_check

    #astros = Client(
    #    server=ASTROS_REST,
    #    route=ROUTE,
    #    data_service=ASTROS_DATA
    #)
    output_dir = os.path.join(os.path.dirname(__file__), "output")
    if not os.path.exists(output_dir):
        os.mkdir(output_dir)
    result = client.exec(input, output_dir=output_dir)
    pytest_check.is_not_none(result)
    pytest_check.is_true(os.path.exists(result))
