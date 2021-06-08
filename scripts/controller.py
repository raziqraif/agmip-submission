from __future__ import annotations  # Delay the evaluation of undefined types

import ipywidgets as ui


class Controller:
    def __init__(self):
        # Import MVC classes here to prevent circular import problem
        from .model import Model
        from .view import View

        self.model: Model
        self.view: View

    def intro(self, model: Model, view: View) -> None:  # type: ignore # noqa
        """Introduce MVC modules to each other"""
        self.model = model
        self.view = view

    def start(self) -> None:
        """Load data, build UI"""
        self.view.display()

    def onchange_ua_file_label(self, change: dict) -> None:
        """Value of the hidden file label in upload area (ua) changed"""
        file_name = change["new"]
        self.view.set_uploaded_filename(file_name)

    def onclick_remove_file(self, widget: ui.Button) -> None:
        """'x' button in the file upload snackbar was clicked"""
        self.view.set_uploaded_filename(None)

    def onclick_download(self, widget: ui.Button) -> None:
        """User clicked on the download button"""
        pass
