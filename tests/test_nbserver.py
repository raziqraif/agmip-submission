import base64
import json
import os
from typing import Optional
import urllib
import pytest
from pathlib import Path


@pytest.fixture
def nbserver_raw_info() -> Optional[str]:
    """
    format:
    nbserver_raw_info -> nbserver_url :: launch_dirpath
    nbserver_url -> nbserver_base_url/?token=token
    launch_dirpath -> /../../launch_dir
    """

    stream = os.popen("jupyter notebook list")

    # output -> <title>:\nnbserver_raw_info\nnbserver_raw_info\n...
    output: str = stream.read()

    if "http" not in output:  # no server is running
        return None

    # output -> nbserver_raw_info
    output = output.split("\n")[1]  # assume our nbserver is at the top
    return output


@pytest.fixture
def nbserver_url(nbserver_raw_info) -> Optional[str]:
    if nbserver_raw_info:
        return nbserver_raw_info.split(" :: ")[0]
    return None


@pytest.fixture
def launch_dirpath(nbserver_raw_info) -> Optional[str]:
    if nbserver_raw_info:
        return nbserver_raw_info.split(" :: ")[1]
    return None


def test_nbserver_launch_dirpath(launch_dirpath):
    """ If notebook server is not launched from proj directory, file upload to workingdir/ will fail """

    project_dir: Path = Path(__file__).parent.parent
    if launch_dirpath is None:  # no server is running
        return
    launch_dir: Path = Path(launch_dirpath)
    assert launch_dir == project_dir


def test_file_upload_api(nbserver_url):
    # def jupyter_upload(token, filepath, resourcedstpath, jupyterurl='http://localhost:8888'):
    """
    uploads file to jupyter notebook server
    ----------------------------------------
    :param token:
        the authorization token issued by jupyter for authentification
        (enabled by default as of version 4.3.0)
    :param filepath:
        the file path to the local content to be uploaded

    :param resourcedstpath:
        the path where resource should be placed.
        the destination directory must exist.

    :param jupyterurl:
        the url to the jupyter server. default value is typical localhost installation.

    :return: server response
    """
    pass
    # file_destination_path = "workingdir/testfile.delete"
    # dstpath = urllib.quote(resourcedstpath)
    # dsturl = "%s/api/contents/%s" % (jupyterurl, dstpath)
    # filename = filepath[1 + filepath.rfind(os.sep) :]
    # headers = {}
    # headers["authorization"] = "token " + token
    # with open(filepath, "r") as myfile:
    #     data = myfile.read()
    #     b64data = base64.encodestring(data)
    #     body = json.dumps(
    #         {"content": b64data, "name": filename, "path": resourcedstpath, "format": "base64", "type": "file"}
    #     )
    #     return requests.put(dsturl, data=body, headers=headers, verify=true)