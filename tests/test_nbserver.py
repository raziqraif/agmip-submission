import base64
import json
import os
from typing import Optional
import urllib
import pytest
from pathlib import Path
import requests


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

    if "http" not in output:  # No server is running
        print("running servers =", output)
        return None

    # output -> NBSERVER_RAW_INFO
    output = output.split("\n")[1]  # assume our nbserver is at the top
    return output


def nbserver_url() -> Optional[str]:
    raw_info = nbserver_raw_info()
    if raw_info:
        return raw_info.split(" :: ")[0]
    return None  # No server is running


def nbserver_baseurl() -> Optional[str]:
    server_full_url = nbserver_url()
    if server_full_url:
        return server_full_url.split("/?token=")[0]
    return None  # No server is running


@pytest.fixture
def nbserver_baseurl_f() -> Optional[str]:
    return nbserver_baseurl()


def nbserver_token() -> Optional[str]:
    server_full_url = nbserver_url()
    if server_full_url:
        return server_full_url.split("/?token=")[1]
    return None  # No server is running


@pytest.fixture
def nbserver_token_f() -> Optional[str]:
    return nbserver_token()


@pytest.fixture
def nbserver_launch_dirpath() -> Optional[Path]:
    raw_info = nbserver_raw_info()
    if raw_info:
        return Path(raw_info.split(" :: ")[1])
    return None


def nb_url() -> Optional[str]:
    server_baseurl = nbserver_baseurl()
    server_token = nbserver_token()
    if server_baseurl and server_token:
        NOTEBOOK_TITLE = "agmip-submission.ipynb"
        return server_baseurl + "/notebooks/" + NOTEBOOK_TITLE + "?token=" + server_token
    return None


def test_nbserver_running():
    assert nbserver_raw_info() is not None


def test_nbserver_launch_dirpath(nbserver_launch_dirpath: Path) -> None:
    """
    If notebook server is not launched from proj directory, file upload will fail
    """

    project_dirpath: Path = Path(__file__).parent.parent
    if nbserver_launch_dirpath is None:  # No server is running
        assert False
    assert nbserver_launch_dirpath == project_dirpath


def test_jupyter_file_upload_api(nbserver_baseurl_f: str, nbserver_token_f: str) -> None:
    # Test file upload method that we're using in the Javascript env
    if nbserver_baseurl_f is None:  # No server is running
        assert False

    # Create new file
    NEWFILE_NAME = "abcdefghij123"

    newfile_path = Path(NEWFILE_NAME)
    newfile = open(NEWFILE_NAME, "w+")
    assert newfile

    # Check upload destination
    uploaddir_path = Path(__name__).parent.parent / "workingdir" / "uploads"  # <project_dir>/workingdir/uploads
    newfiledest_path = Path(uploaddir_path / NEWFILE_NAME)

    if newfiledest_path.exists():
        newfiledest_path.unlink()
    assert newfiledest_path.exists() == False

    # Upload file
    fileupload_dest = "workingdir/uploads/" + NEWFILE_NAME
    url = nbserver_baseurl_f + "/api/contents/" + fileupload_dest
    print("url =", url)
    headers = {}
    headers["authorization"] = "token " + nbserver_token_f
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
