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
        if len(file_name) == 0:  # This change was triggered by View's internal operation, so no View update is needed
            return

        self.model.uploaded_filename = file_name
        if file_name.endswith(CSV):
            self.view.show_notification(Notification.SUCCESS, Notification.FILE_UPLOAD_SUCCESS)
            self.view.update_file_upload_page(file_name)
        else:
            self.view.show_notification(Notification.ERROR, Notification.INVALID_FILE_FORMAT)
            self.model.remove_file(file_name)
            self.model.uploaded_filename = ""

    def onclick_remove_file(self, widget: ui.Button) -> None:
        """'x' button in the file upload snackbar was clicked"""
        assert len(self.model.uploaded_filename) > 0
        self.model.remove_file(self.model.uploaded_filename)
        self.model.uploaded_filename = ""
        self.view.update_file_upload_page(None)

    def onclick_next_from_page_1(self, widget: ui.Button) -> None:
        """'Next' button on the file upload page was clicked"""
        if len(self.model.uploaded_filename) == 0:
            self.view.show_notification(Notification.INFO, Notification.PLEASE_UPLOAD)
            return
        self.view.set_progress_cursor_style()
        if self.model.finished_steps == 0:
            self.model.finished_steps += 1
            error_message = self.model.load_file(self.model.uploaded_filename)
            self.view.update_data_specification_page()
            if error_message is not None:
                self.view.show_notification(Notification.ERROR, error_message)
            else:
                self.view.show_notification(Notification.INFO, "Some fields have been prepopulated for you")
        self.view.reset_cursor_style()
        self.view.switch_page(2)
