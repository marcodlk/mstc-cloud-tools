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

## What About The Rest of The Module?

Aside `nslookup`, which is an exact copy of what is in `mstc-web-astros`, the
rest of the module can be ignored for now as it is not quite ready yet.
Although the code logic is mostly the same as what is in 
`mstc-web-astros` at the time of this writing, there are some slight
modifications being experimented.

### What is different

The changes being experimented with have the goal of giving the **option**
to create an app from the "exec command" logic as concisely as possible,
while also allowing for creating the app from the ground up using the
Provider as well.

#### ClientProxy & ServerProxy

The `ClientProxy` is responsible for converting the client inputs into
requests and server responses to outputs. Conversely, the `ServerProxy`
is responsible for converting the client requests into provider inputs
and provider outputs to server responses. The goal is to abstract the
transport layer such that the client and provider may be implemented
assuming that the provider sees essentially the same inputs that the
client sends and the client sees the same outputs the provider returns
-- agnostic to the details of how the data is transmitted between them.

The following flow chart illustrates the IPC flow:

![Flowchart](/docs/assets/images/client_to_provider_flow.png?raw=true)

If we include the data service:

![Flowchart with DataService](/docs/assets/images/client_to_provider_ds_flow.png?raw=true)
```