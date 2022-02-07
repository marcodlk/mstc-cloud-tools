# mstc-cloud-tools

The `mstc_cloud_tools` package provides tools for the development and usage
of Engineering Application Providers.

### Prerequisites

* [Poetry](https://python-poetry.org), for dependency management.

### Installation

In the project directory, run:
```
poetry install
```

## Usage

### Client

The client currently only communicates with one endpoint, the "exec" endpoint.
To initialize the client, provide the server url string (protocol agnostic),
"exec" endpoint route, and data service url.
```python
from mstc_cloud_tools import Client

client = Client(
    server="localhost:31001",
    route="mstc/astros/exec",
    data_service="localhost:31002"
)
```

To check whether the client is inside the cluster, use the `inside_cluster`
method.
```python
from mstc_cloud_tools import inside_cluster

if inside_cluster():
    client = Client(
        server="mstc-astros-service:8080/",
        route="mstc/astros/exec"
    )
```

To execute the RPC, use the `exec` method:
```python
output_filename = client.exec(["astrosInput.dat", "astrosInput.bdf"])
```

### Client Integration Tests

The `Client` works with the current version of `mstc-web-astros` as of this
writing. This can be verified by running
the integration tests, assumming that `mstc-web-astros` is deployed.
```bash
pytest integration_tests/mstc-web-astros/
```