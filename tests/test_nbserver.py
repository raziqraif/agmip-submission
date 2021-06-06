import base64
import json
import os
from typing import Optional
import urllib
import pytest
from pathlib import Path
import requests


@pytest.fixture
def nbserver_raw_info() -> Optional[str]:
    """
    Format:
    NBSERVER_RAW_INFO -> NBSERVER_URL :: LAUNCH_DIRPATH
    NBSERVER_URL -> NBSERVER_BASE_URL/?token=TOKEN
    LAUNCH_DIRPATH -> /../../LAUNCH_DIR
    """

    # Conda activation doesn't work well with vscode, so hard code this for now
    stream = os.popen("/Users/raziqraif/opt/anaconda3/envs/agmip/bin/jupyter notebook list")

    # output -> <title>:\nNBSERVER_RAW_INFO\nNBSERVER_RAW_INFO\n...
    output: str = stream.read()

    if "http" not in output:  # No server is running
        return None

    # output -> NBSERVER_RAW_INFO
    output = output.split("\n")[1]  # assume our nbserver is at the top
    return output


@pytest.fixture
def nbserver_url(nbserver_raw_info) -> Optional[str]:
    if nbserver_raw_info:
        return nbserver_raw_info.split(" :: ")[0]
    return None  # No server is running


@pytest.fixture
def nbserver_baseurl(nbserver_url) -> Optional[str]:
    if nbserver_url:
        return nbserver_url.split("/?token=")[0]
    return None  # No server is running


@pytest.fixture
def nbserver_token(nbserver_url) -> Optional[str]:
    if nbserver_url:
        return nbserver_url.split("/?token=")[1]
    return None  # No server is running


@pytest.fixture
def launch_dirpath(nbserver_raw_info) -> Optional[str]:
    if nbserver_raw_info:
        return nbserver_raw_info.split(" :: ")[1]
    return None


def test_nbserver_launch_dirpath(launch_dirpath):
    """
    If notebook server is not launched from proj directory, file upload will fail
    """

    project_dir: Path = Path(__file__).parent.parent
    if launch_dirpath is None:  # No server is running
        return
    launch_dir: Path = Path(launch_dirpath)
    assert launch_dir == project_dir


def test_jupyter_file_upload_api(nbserver_baseurl, nbserver_token):
    if nbserver_url is None:  # No server is running
        return

    # Prepare file to upload

    TEMP_FILE_NAME = "abcdefghij123"
    if Path(TEMP_FILE_NAME).exists():
        Path(TEMP_FILE_NAME).unlink()

    temp_file_path = Path(TEMP_FILE_NAME)
    temp_file = open(TEMP_FILE_NAME, "w+")
    assert temp_file

    uploads_dirpath = Path(__name__).parent.parent / Path("uploads")  # <project_dir>/uploads
    uploaded_temp_filepath = Path(uploads_dirpath / TEMP_FILE_NAME)

    if uploaded_temp_filepath.exists():
        uploaded_temp_filepath.unlink()
    assert uploaded_temp_filepath.exists() == False

    # Upload file

    file_destination_path = "uploads/" + TEMP_FILE_NAME
    url = nbserver_baseurl + "/api/contents/" + file_destination_path
    print("url =", url)
    headers = {}
    headers["authorization"] = "token " + nbserver_token
    file_content = temp_file.read()
    file_content = file_content.encode("ascii")
    base64_file_content = base64.b64encode(file_content)
    base64_file_content = base64_file_content.decode("ascii")

    body = json.dumps(
        {
            "content": base64_file_content,
            "name": TEMP_FILE_NAME,
            "path": file_destination_path,
            "format": "base64",
            "type": "file",
        }
    )
    response = requests.put(url, data=body, headers=headers, verify=True)
    
    assert response.status_code == 201
    assert uploaded_temp_filepath.exists() == True
    temp_file_path.unlink()
    uploaded_temp_filepath.unlink()