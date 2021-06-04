from __future__ import annotations  # Delay the evaluation of undefined types
import os


def get_server_auth_token() -> str:
    """Get auth token to interact with notebook server's API"""

    # Terminal command to print the urls of running servers.
    stream = os.popen("jupyter notebook list")
    output = stream.read()

    # Assume our server is at the top of the output and extract its token
    # If all notebook servers on mygeohub are guaranteed to launched from the user directory, having
    # this assumption is fine, since we only need the token to upload file into the user directory

    # TODO: Verify that this assumption won't cause complication 

    # Format of output is "...http://SERVER_URL/?token=TOKEN :: ..."
    output = output.split("token=")[1]

    # Format of output is "TOKEN :: ..."
    token = output.split(" ")[0]
    return token


class Model:

    JUPYTER_TOKEN: str = get_server_auth_token()

    def __init__(self):
        # Import MVC classes here to prevent circular import problem
        from .controller import Controller
        from .view import View

        self.view: View
        self.controller: Controller

    def intro(self, view: View, controller: Controller) -> None:  # type: ignore
        """Introduce MVC modules to each other"""
        self.view = view
        self.controller = controller
