"""Hostname provider app."""

import os

from mstc_cloud_tools.provider import BaseProvider

PORT = 8080
DATASERVICE_PORT = 8081

THIS_DIR = os.path.dirname(os.path.realpath(__file__))

class HostnameProvider(BaseProvider):
    def get_exec_command(script_to_exec, native_dir, inputs):
        script_to_exec = THIS_DIR + "/script.py"
        outfile = "hostname.out"
        return ["python", script_to_exec, "hostname", outfile], [outfile]

def create_app():
    pass

if __name__ == "__main__":
    app = HostnameProvider().create_app(data_service_port=DATASERVICE_PORT)
    app.run(port=PORT)