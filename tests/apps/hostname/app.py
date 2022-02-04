"""Hostname provider app."""

import os

from mstc_cloud_tools.provider import BaseProvider
from mstc_cloud_tools import create_app

PORT = 8080
DATASERVICE_PORT = 8081

THIS_DIR = os.path.dirname(os.path.realpath(__file__))

class HostnameProvider(BaseProvider):
    def get_exec_command(self, script_to_exec, native_dir, inputs):
        # script_to_exec = THIS_DIR + "/script.py"
        outfile = "hostname.out"
        return ["python", script_to_exec, "hostname", outfile], [outfile]

    def get_native_app_runner_path(self):
        return os.path.join(THIS_DIR, "script.py")

def create_hostname_app(scratch_dir):
    app, port = create_app(
        HostnameProvider, __name__, 
        scratch_dir=scratch_dir, data_service_port=DATASERVICE_PORT)
    return app

if __name__ == "__main__":
    create_hostname_app().run(port=PORT)