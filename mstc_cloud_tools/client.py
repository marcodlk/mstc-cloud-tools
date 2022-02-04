import json
import os
import socket
from pathlib import Path

import requests

from mstc_cloud_tools import data_service, nslookup


class ClientProxy:
    def __init__(self, data_service_url, endpoint, output_dir, data_url):
        self.endpoint = endpoint
        self.data_service_url = data_service_url
        self.output_dir = output_dir
        self.data_url = data_url

    def submit_inputs(self, inputs):
        request = self.inputs_to_request(inputs)
        response = self.submit_request(request)
        return self.response_to_outputs(response)

    def submit_request(self, request):
        headers = {"Content-type": "application/json"}
        response = requests.post(
            self.endpoint, data=json.dumps(request), headers=headers
        )
        if response.status_code == 200:
            return response.json()
        else:
            print(str(response.status_code) + ": " + response.text)
            return None

    def inputs_to_request(self, inputs):
        url_inputs = []
        for input in inputs:
            url_inputs.append(self.data_service_url + "/" + os.path.basename(input))
        return url_inputs

    def response_to_outputs(self, response):
        data_url = self.data_url
        output_urls = response["outputs"]
        if self.output_dir is not None:
            from urllib.parse import urlparse
            files = []
            for output_url in output_urls:
                a = urlparse(output_url)
                if data_url is None:
                    data_url = output_url
                else:
                    data_url = data_url[:-1] if data_url.endswith("/") else data_url
                    data_url = data_url + a.path
                       
                file_name = os.path.basename(a.path)
                content = requests.get(data_url)
                output_file = os.path.join(self.output_dir, file_name)
                with open(output_file, "wb") as f:
                    f.write(content.content)
                files.append(os.path.abspath(output_file))
            return files
        else:
            return output_urls


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

        # TODO: currently assumes all inputs share same parent dir
        root_dir = ""
        for input in inputs:
            if os.path.exists(input):
                root_dir = Path(input).parent.absolute()
            else:
                raise FileNotFoundError(input + " not found")

        ds = data_service.DataService(root_dir, 0, client_addr)
        ds_server, data_service_url = ds.start()

        client_proxy = ClientProxy(data_service_url, endpoint, output_dir, data_url)
        try:
            outputs = client_proxy.submit_inputs(inputs)
        finally:
            ds_server.shutdown()

        return outputs


def inside_cluster():
    fqdn = nslookup.find(socket.gethostbyname(socket.gethostname()))
    return fqdn and "svc.cluster" in fqdn


def normalize_partial_url(url):
    if  url is None:
        return url
    if not url[-1] == "/":
        return url + "/"
    else:
        return url
