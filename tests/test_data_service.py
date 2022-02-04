import os
from pathlib import Path

import pytest

from mstc_cloud_tools.data_service import DataService

def test_data_service_ok():
    import requests
    from pytest_check import is_not_none

    path = Path(os.path.dirname(__file__))
    files_dir = os.path.join(path, "files")
    ds = DataService(files_dir)
    server, url = ds.start()
    is_not_none(server)
    is_not_none(url)
    r = requests.get(url + "/helloworld.txt")
    assert r.status_code == 200


def test_data_service_bad():
    import requests
    from pytest_check import is_not_none

    ds = DataService(os.path.dirname(__file__))
    server, url = ds.start()
    is_not_none(server)
    is_not_none(url)
    r = requests.get(url + "/../../../../../../tmp/foo.txt")
    assert r.status_code == 404


def test_data_service_bad_directory():

    with pytest.raises(IOError):
        DataService("flibity-gibity")