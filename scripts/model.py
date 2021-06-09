from __future__ import annotations  # Delay the evaluation of undefined types
import os
from pathlib import Path
from typing import Union


def get_notebook_auth_token() -> str:
    """Get auth token to interact with notebook server's API"""

    # Terminal command to print the urls of running servers.
    stream = os.popen("jupyter notebook list")
    output = stream.read()

    # Assume our server is at the top of the output and extract its token

    # Format of output is "...http://SERVER_URL/?token=TOKEN :: ..."
    output = output.split("token=")[1]

    # Format of output is "TOKEN :: ..."
    token = output.split(" ")[0]
    return token


class JSAppModel:
    def __init__(self):
        # Auth token of notebook server
        self.nbserver_auth_token: str = get_notebook_auth_token()

        # Model ID of the label in "UA" (upload area) which displays the most recently uploaded file name.
        # This label is actually hidden and only used for communication between js & python.
        self.ua_file_label_model_id: str = ""


class Model:
    UPLOAD_DIR: Path = Path(__name__).parent.parent / Path("uploads")  # <PROJECT_DIR>/uploads

    def __init__(self):
        # Import MVC classes here to prevent circular import problem
        from .controller import Controller
        from .view import View

        self.view: View
        self.controller: Controller

        self._js_app_model = JSAppModel()

        self.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

    def intro(self, view: View, controller: Controller) -> None:  # type: ignore # noqa
        """Introduce MVC modules to each other"""
        self.view = view
        self.controller = controller

    def update_javascript_app_model(self, attr_name: str, attr_value: str) -> None:
        """Update an attribute of the app model in Javascript"""
        assert attr_name in vars(self._js_app_model).keys()
        setattr(self._js_app_model, attr_name, attr_value)

    def javascript_app_model(self) -> str:
        """Get the string representation of the app model in Javascript"""
        return str(vars(self._js_app_model))

    def remove_file(self, file_name: str) -> None:
        """Remove uploaded file from the upload directory"""
        assert len(file_name) > 0
        file_path = self.UPLOAD_DIR / Path(file_name)
        assert file_path.is_file()
        file_path.unlink()
