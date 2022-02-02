import json
import os
import socket
from pathlib import Path

import requests

from mstc_cloud_tools import data_service, nslookup


class Client:
    def __init__(self, server, route, data_service=None):
        self.server_url = normalize_partial_url(server)
        self.data_url = normalize_partial_url(data_service)
        self.route = route
    
    def exec(self, inputs, **kwargs):

        client_addr = kwargs.get("client_addr")
        if client_addr is None:
            client_addr = "0.0.0.0"

        endpoint = kwargs.get("endpoint")
        if endpoint is None:
            endpoint = "http://" + self.server_url + self.route

        output_dir = kwargs.get("output_dir")

        data_url = kwargs.get("data_url", self.data_url)
        if data_url is not None:
            data_url = "http://" + data_url

        root_dir = ""
        for input in inputs:
            if os.path.exists(input):
                root_dir = Path(input).parent.absolute()
            else:
                raise FileNotFoundError(input + " not found")

        ds = data_service.DataService(root_dir, 0, client_addr)
        ds_server, data_service_url = ds.start()

        url_inputs = []
        for input in inputs:
            url_inputs.append(data_service_url + "/" + os.path.basename(input))

        try:
            headers = {"Content-type": "application/json"}
            response = requests.post(endpoint, data=json.dumps(url_inputs), headers=headers)
            if response.status_code == 200:
                result = response.json()
                output_url = result["outputs"]
                if output_dir is not None:
                    from urllib.parse import urlparse

                    a = urlparse(output_url[0])
                    if data_url is None:
                        data_url = output_url[0]
                    else:
                        data_url = data_url[:-1] if data_url.endswith("/") else data_url
                        data_url = data_url + a.path

                    file_name = os.path.basename(a.path)
                    content = requests.get(data_url)
                    output_file = os.path.join(output_dir, file_name)
                    with open(output_file, "wb") as f:
                        f.write(content.content)
                    return os.path.abspath(output_file)
                else:
                    return output_url[0]
            else:
                print(str(response.status_code) + ": " + response.text)

        finally:
            ds_server.shutdown()

        return None


def inside_cluster():
    fqdn = nslookup.find(socket.gethostbyname(socket.gethostname()))
    return fqdn and "svc.cluster" in fqdn


def normalize_partial_url(url):
    if not url[-1] == "/":
        return url + "/"
    else:
        return url
