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

    # Assumption: 'jupyter' can be found by system without having to activate conda environment explicitly
    stream = os.popen("jupyter notebook list")
    # output -> <title>:\nNBSERVER_RAW_INFO\nNBSERVER_RAW_INFO\n...
    output: str = stream.read()

    print("command output =", output)
    if "http" not in output:  # No server is running
        return None

    # output -> NBSERVER_RAW_INFO
    output = output.split("\n")[1]  # assume our nbserver is at the top
    return output


@pytest.fixture
def nbserver_url(nbserver_raw_info: str) -> Optional[str]:
    if nbserver_raw_info:
        return nbserver_raw_info.split(" :: ")[0]
    return None  # No server is running


@pytest.fixture
def nbserver_baseurl(nbserver_url: str) -> Optional[str]:
    if nbserver_url:
        return nbserver_url.split("/?token=")[0]
    return None  # No server is running


@pytest.fixture
def nbserver_token(nbserver_url: str) -> Optional[str]:
    if nbserver_url:
        return nbserver_url.split("/?token=")[1]
    return None  # No server is running


@pytest.fixture
def nbserver_launch_dirpath(nbserver_raw_info: str) -> Optional[Path]:
    if nbserver_raw_info:
        return Path(nbserver_raw_info.split(" :: ")[1])
    return None


def test_nbserver_launch_dirpath(nbserver_launch_dirpath: Path) -> None:
    """
    If notebook server is not launched from proj directory, file upload will fail
    """

    project_dirpath: Path = Path(__file__).parent.parent
    if nbserver_launch_dirpath is None:  # No server is running
        return
    assert nbserver_launch_dirpath == project_dirpath


def test_jupyter_file_upload_api(nbserver_baseurl: str, nbserver_token: str) -> None:
    # Test file upload method that we're using in the Javascript env

    if nbserver_baseurl is None:  # No server is running
        return

    # Create new file
    NEWFILE_NAME = "abcdefghij123"

    newfile_path = Path(NEWFILE_NAME)
    newfile = open(NEWFILE_NAME, "w+")
    assert newfile

    # Check upload destination
    uploaddir_path = Path(__name__).parent.parent / Path("uploads")  # <project_dir>/uploads
    newfiledest_path = Path(uploaddir_path / NEWFILE_NAME)

    if newfiledest_path.exists():
        newfiledest_path.unlink()
    assert newfiledest_path.exists() == False

    # Upload file
    fileupload_dest = "uploads/" + NEWFILE_NAME
    url = nbserver_baseurl + "/api/contents/" + fileupload_dest
    print("url =", url)
    headers = {}
    headers["authorization"] = "token " + nbserver_token
    file_content = newfile.read()
    file_content = file_content.encode("ascii")
    base64_file_content = base64.b64encode(file_content)
    base64_file_content = base64_file_content.decode("ascii")

    body = json.dumps(
        {
            "content": base64_file_content,
            "name": NEWFILE_NAME,
            "path": fileupload_dest,
            "format": "base64",
            "type": "file",
        }
    )
    response = requests.put(url, data=body, headers=headers, verify=True)

    # Test & cleanup
    assert response.status_code == 201  # HTTP created
    assert newfiledest_path.exists() == True
    newfile_path.unlink()
    newfiledest_path.unlink()
