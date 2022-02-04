import os
import logging
import time
from datetime import datetime
import traceback
import urllib.error
from abc import ABC, abstractmethod

from flask import Flask, g, render_template, request, current_app
from flask_api import status

from mstc_cloud_tools import nslookup


class InputValidator:

    def __init__(self, logger):
        self.logger = logger

    def validate(self, inputs):
        valid = True
        message = None
        return valid, message


class ServerProxy:

    def __init__(self, data_service_url: str, scratch_dir: str, logger: logging.Logger):
        self.data_service_url = data_service_url
        self.scratch_dir = scratch_dir
        self.logger = logger

    def request_to_inputs(self, json_data, exec_dir):
        inputs = []
        for input in json_data:
            if input.startswith("http"):
                import urllib.parse
                import urllib.request

                self.logger.info("Get input: " + input)
                u = urllib.parse.urlparse(input)
                ndx = u.path.rfind("/")
                dir = exec_dir + u.path[0:ndx]
                if not os.path.exists(dir):
                    os.makedirs(dir)
                self.logger.info("Created dir: " + os.path.abspath(dir))
                file_name = exec_dir + u.path
                try:
                    self.logger.debug("Opening file: " + file_name)
                    input_file = open(file_name, "wb")
                    self.logger.debug("Opening url: " + str(input))
                    req_url = urllib.request.urlopen(input)
                    self.logger.debug("Writing file: " + file_name)
                    input_file.write(req_url.read())
                    input_file.close()
                    self.logger.info("Wrote to file " + file_name)
                except urllib.error.HTTPError as e:
                    self.logger.info("The server could not fulfill the request. Error code: " + e.code)
                    self._clean(file_name)
                    raise urllib.error.HTTPError("failed accessing: " + input) from e
                except urllib.error.URLError as e:
                    self.logger.info("We failed to reach a server. Reason: " + str(e.reason))
                    self._clean(file_name)
                    raise urllib.error.URLError("failed accessing: " + input) from e

                inputs.append(file_name)
            else:
                if os.path.exists(input):
                    import shutil

                    dst = os.path.join(exec_dir, os.path.basename(input))
                    shutil.copyfile(input, dst)
                    inputs.append(dst)
                else:
                    raise FileNotFoundError(input + " not found")

        return inputs

    def outputs_to_response(self, output_file_names, exec_dir):
        output_file_urls = []
        for output_file in output_file_names:
            for filename in os.listdir(exec_dir):
                if filename == output_file:
                    relative_path = exec_dir[len(self.scratch_dir):]
                    request_path = self.data_service_url + relative_path
                    output_file_urls.append(request_path + "/" + filename)

        if len(output_file_urls) == len(output_file_names):
            return {"outputs": output_file_urls}

        return (
            "Could not find all output files " + str(output_file_names),
            status.HTTP_404_NOT_FOUND,
        )

    def _clean(self, file):
        try:
            if os.path.exists(file):
                os.remove(file)
        except Exception as e:
            print("Oops: " + str(e))
            pass


class BaseProvider(ABC):

    input_validator_class = InputValidator
    exec_endpoint = "/exec"

    @classmethod
    def setUp(cls, scratch_dir, native_dir, data_service_url):
        cls.counter = 1
        cls.scratch_dir = scratch_dir
        cls.native_dir = native_dir
        cls.data_service_url = data_service_url

    @classmethod
    def init_app(cls, app, scratch_dir=None, native_dir=None, data_service_port=8081):
        
        native_dir = native_dir or "/app/native"
        scratch_dir = scratch_dir or os.path.join(os.getcwd(), "scratch")

        logging.basicConfig(format="%(asctime)s %(message)s", level=logging.INFO)
        if not os.path.exists(scratch_dir):
            os.makedirs(scratch_dir)
            app.logger.info("Created dir: " + scratch_dir)
        _, data_service_url = _create_data_service(scratch_dir, data_service_port)
        app.logger.info("Data service serving on: " + data_service_url)
        cls.setUp(scratch_dir, native_dir, data_service_url)

        app.config["SCRATCH_DIR"] = scratch_dir
        app.config["STATS"] = dict()
        app.config["START_TIME"] = datetime.utcnow()
        
        cls.init_endpoints(app)
        cls.init_path_stats(app)

    @classmethod
    def init_endpoints(cls, app):

        @app.route("/", methods=["GET"])
        def index():
            return cls().index()

        @app.route(cls.exec_endpoint, methods=["POST"])
        def exec():
            if not request.is_json:
                message = "Request is not json"
                current_app.logger.warning(message)
                return message, status.HTTP_400_BAD_REQUEST

            provider = cls()
            return provider.exec(request.get_json())

        @app.errorhandler(Exception)
        def basic_error(e):
            return "An error occured: " + str(e), status.HTTP_500_INTERNAL_SERVER_ERROR

        @app.before_request
        def before_request():
            g.start = time.time()
            current_app.config["STATS"][request.path]._count += 1

        @app.after_request
        def after_request(response):
            if request.path == "/favicon.ico":
                return response
            duration = round(time.time() - g.start, 3)
            host = request.host.split(":", 1)[0]
            log_params = [("duration", str(duration) + " ms,"), ("from", host + ","), ("status", response.status_code)]
            parts = []
            for name, value in log_params:
                part = "{}: {}".format(name, value)
                parts.append(part)
            stats = " ".join(parts)
            current_app.logger.info(request.method + " " + request.path + ", " + stats)

            current_app.config["STATS"][request.path].add_values(duration, response.status_code)

            return response

    @classmethod
    def init_path_stats(cls, app):
        for r in app.url_map.iter_rules():
            path_stats = PathStats()
            app.config["STATS"][str(r)] = path_stats

    def index(self):
        values = self.info()
        stats = self.stats
        return render_template("index.html", values=values, stats=stats)

    def info(self):
        import socket

        start_time = self.start_time
        addr = socket.gethostbyname(socket.gethostname())
        hostname = nslookup.find(addr)
        when = datetime.utcnow()
        uptime = when - start_time
        self.logger.info("hello from " + str(request.remote_addr))
        values = {
            "addr": addr,
            "hostname": hostname,
            "remote_addr": request.remote_addr,
            "when": when.strftime("%Y-%m-%d %H:%M:%S"),
            "started": start_time.strftime("%Y-%m-%d %H:%M:%S"),
            "uptime": uptime,
        }
        return values

    def exec(self, json_data):

        server_proxy = ServerProxy(self.data_service_url, self.scratch_dir, self.logger)
        try:
            exec_dir = self._create_exec_dir()
            inputs = server_proxy.request_to_inputs(json_data, exec_dir)

            valid, message = self.input_validator_class(self.logger).validate(json_data)
            if not valid:
                message = "Inputs are not valid, " + message
                self.logger.warning(message)
                return message, status.HTTP_400_BAD_REQUEST

            script_command, output_file_names = self._copy_script_and_get_command(exec_dir, self.native_dir, inputs)

            completed = self._exec_native_app(exec_dir, script_command, env={})
            self.logger.debug("return_code: " + str(completed.returncode))
            self.logger.debug("stdout:\n" + str(completed.stdout.decode("utf-8")))
            if completed.returncode != 0:
                error_message = (
                    "Service execution failed. Return code: "
                    + str(completed.returncode)
                    + "\n"
                    + str(completed.stdout.decode("utf-8"))
                )
                self.logger.warning(error_message + ", exec_dir: " + exec_dir)
                return error_message, status.HTTP_500_INTERNAL_SERVER_ERROR

            return server_proxy.outputs_to_response(output_file_names, exec_dir)

        except (FileNotFoundError, urllib.error.URLError, urllib.error.HTTPError) as e:
            error_message = "Bad input: " + str(e)
            failure = {"failure": error_message + "\n" + traceback.format_exc()}
            self.logger.warning(failure)
            return error_message, status.HTTP_400_BAD_REQUEST

        except ValueError as e:
            error_message = "Decoding JSON has failed: " + str(e)
            failure = {"failure": error_message + "\n" + traceback.format_exc()}
            self.logger.warning(failure)
            raise

        except Exception as e:
            self.logger.warning(traceback.format_exc())
            error_message = "Exception caught submitting to application: " + str(e)
            failure = {"failure": error_message + "\n" + traceback.format_exc()}
            self.logger.warning(failure)
            raise

    def _create_exec_dir(self):

        when = datetime.utcnow().strftime("%Y-%m-%d,%H:%M:%S.%f")
        exec_dir = os.path.join(self.scratch_dir, "exec-" + str(self.counter) + "-" + when)
        self.__class__.counter += 1
        if not os.path.exists(exec_dir):
            os.makedirs(exec_dir)
            self.logger.info("Created exec dir: " + exec_dir)
        return exec_dir

    def _exec_native_app(self, exec_dir, cmd_to_exec, env):
        import subprocess

        self.logger.info("Running: " + str(cmd_to_exec))
        print("Running: " + str(cmd_to_exec))
        return subprocess.run(cmd_to_exec, cwd=exec_dir, capture_output=True, env=env)

    def _copy_script_and_get_command(self, exec_dir, native_dir, inputs):
        import shutil
        import stat
        # from pathlib import Path

        # path = Path(os.path.dirname(__file__))
        # src = os.path.join(path.parent.absolute(), "bin/native-app-runner.sh")
        src = self.get_native_app_runner_path()
        dst = os.path.join(exec_dir, os.path.basename(src))
        self.logger.info("Copy " + src + " -> " + dst)
        shutil.copyfile(src, dst)
        st = os.stat(dst)
        os.chmod(dst, st.st_mode | stat.S_IEXEC)

        return self.get_exec_command(dst, native_dir, inputs)
    
    def get_native_app_runner_path(self):
        from pathlib import Path

        path = Path(os.path.dirname(__file__))
        return os.path.join(path.parent.absolute(), "bin/native-app-runner.sh")

    @abstractmethod
    def get_exec_command(script_to_exec, native_dir, inputs):
        pass

    @property
    def start_time(self):
        return current_app.config["START_TIME"]

    @property
    def stats(self):
        return current_app.config["STATS"]

    @property
    def app(self) -> Flask:
        return current_app

    @property
    def logger(self) -> logging.Logger:
        return current_app.logger


class PathStats:
    def __init__(self):
        self._longest = 0.0
        self._shortest = 0.0
        self._last = 0.0
        self._count = 0
        self._errors = 0

    def add_values(self, duration, status):
        if self._count == 1:
            self._longest = duration
            self._shortest = duration
        else:
            self._longest = duration if duration > self._longest else self._longest
            self._shortest = duration if duration < self._shortest else self._shortest
        self._last = duration
        if status != 200:
            self._errors += 1

    def longest(self):
        return self._longest

    def shortest(self):
        return self._shortest

    def last(self):
        return self._last

    def count(self):
        return self._count

    def errors(self):
        return self._errors


def _create_data_service(scratch_dir, port_arg, ip="0.0.0.0"):
    from mstc_cloud_tools import data_service

    data_service = data_service.DataService(scratch_dir, port_arg, ip)
    return data_service.start()