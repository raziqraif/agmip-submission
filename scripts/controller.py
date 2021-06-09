from __future__ import annotations  # Delay the evaluation of undefined types

from pathlib import Path
import ipywidgets as ui

from .view import Notification


class Controller:
    def __init__(self):
        # Import MVC classes here to prevent circular import problem
        from .model import Model
        from .view import View

        self.model: Model
        self.view: View

        self._uploaded_filename: str = ""  # Tracks uploaded file name
        # Needs to be updated when the file was removed too

    def intro(self, model: Model, view: View) -> None:  # type: ignore # noqa
        """Introduce MVC modules to each other"""
        self.model = model
        self.view = view

    def start(self) -> None:
        """Load data, build UI"""
        self.view.display()

    def onchange_ua_file_label(self, change: dict) -> None:
        """Value of the hidden file label in upload area (ua) changed"""
        CSV = ".csv"
        file_name: str = change["new"]
        self._uploaded_filename = file_name

        if len(file_name) == 0:  # This change was triggered by View's internal operation, so no View update is needed
            return
        if file_name.endswith(CSV):
            self.view.show_notification(Notification.SUCCESS, "File uploaded successfully")
            self.view.update_file_upload_page(file_name)
        else:
            self.view.show_notification(Notification.ERROR, "File format must be CSV")
            self.model.remove_file(file_name)
            self._uploaded_filename = ""

    def onclick_remove_file(self, widget: ui.Button) -> None:
        """'x' button in the file upload snackbar was clicked"""
        # The order of the following code matters. Because self.view.update_file_upload_page(None) will trigger
        # onchange_ua_file, which will modify the value of self._uploaded_filename
        assert len(self._uploaded_filename) > 0
        self.model.remove_file(self._uploaded_filename)
        self._uploaded_filename = ""
        self.view.update_file_upload_page(None)

    def onclick_next_from_page_1(self, widget: ui.Button) -> None:
        """'Next' button on the file upload page was clicked"""

        if len(self._uploaded_filename) == 0:
            self.view.show_notification(Notification.INFO, "Please upload a CSV file first")
