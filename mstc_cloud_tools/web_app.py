from flask import Flask
from mstc_cloud_tools.provider import BaseProvider

def create_app(
    provider_class: BaseProvider, 
    app_name,
    scratch_dir=None, 
    native_dir=None, 
    data_service_port=8081
):
    app = Flask(app_name)
    provider_class.init_app(app, scratch_dir, native_dir, data_service_port)

    port = 8080
    return app, port
