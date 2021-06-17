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

    def reset_later_steps(self, current_finished_step: int) -> None:
        """Set the last active page to the given argument"""
        if self.model.finished_steps == current_finished_step:
            return
        self.model.finished_steps = current_finished_step
        current_page_number = current_finished_step + 1 
        self.view.switch_page(current_page_number, is_last_active_page=True)

    def validate_data_specification_input(self) -> bool:
        """Return true if all input are entered correctly, and false if not"""
        is_valid = False
        try:
            if len(self.model.model_name) == 0:
                self.view.show_notification(Notification.WARNING, "Please select the model name")
            elif len(self.model.delimiter) == 0:
                self.view.show_notification(Notification.WARNING, "Please select the delimiter")
            elif len(self.model.lines_to_skip) == 0:
                self.view.show_notification(Notification.WARNING, "Please enter the initial number of lines to skip")
            elif int(self.model.lines_to_skip) < 0:
                self.view.show_notification(
                    Notification.WARNING, "Please enter a positive integer for the number of lines to skip"
                )
            elif len(self.model.scenario_column) == 0:
                self.view.show_notification(Notification.WARNING, "Please select the scenario column")
            elif len(self.model.region_column) == 0:
                self.view.show_notification(Notification.WARNING, "Please select the region column")
            elif len(self.model.variable_column) == 0:
                self.view.show_notification(Notification.WARNING, "Please select the variable column")
            elif len(self.model.item_column) == 0:
                self.view.show_notification(Notification.WARNING, "Please select the item column")
            elif len(self.model.unit_column) == 0:
                self.view.show_notification(Notification.WARNING, "Please select the unit column")
            elif len(self.model.year_column) == 0:
                self.view.show_notification(Notification.WARNING, "Please select the year column")
            elif len(self.model.value_column) == 0:
                self.view.show_notification(Notification.WARNING, "Please select the value column")
            elif (
                len(
                    set(
                        [
                            self.model.scenario_column,
                            self.model.region_column,
                            self.model.variable_column,
                            self.model.item_column,
                            self.model.unit_column,
                            self.model.year_column,
                            self.model.value_column,
                        ]
                    )
                )
                < 7
            ):
                self.view.show_notification(Notification.WARNING, "Please assign an input column to only 1 output column")
            else:
                is_valid = True
        except ValueError:
            self.view.show_notification(
                Notification.WARNING, "Please enter an integer for the number of lines to skip"
            )
        return is_valid

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
        self.reset_later_steps(current_finished_step=0)

    def onclick_remove_file(self, widget: ui.Button) -> None:
        """'x' button in the file upload snackbar was clicked"""
        assert len(self.model.uploaded_filename) > 0
        self.model.remove_file(self.model.uploaded_filename)
        self.model.uploaded_filename = ""
        self.view.update_file_upload_page(None)
        self.reset_later_steps(current_finished_step=0)

    def onclick_next_from_page_1(self, widget: ui.Button) -> None:
        """'Next' button on the file upload page was clicked"""
        if len(self.model.uploaded_filename) == 0:
            self.view.show_notification(Notification.INFO, Notification.PLEASE_UPLOAD)
            return
        if self.model.finished_steps == 0:
            self.model.finished_steps = 1
            self.view.set_progress_cursor_style()
            error_message = self.model.load_file(self.model.uploaded_filename)
            self.view.update_data_specification_page()
            if error_message is not None:
                self.view.show_notification(Notification.ERROR, error_message)
            else:
                self.view.show_notification(Notification.INFO, Notification.FIELDS_WERE_PREPOPULATED)
            self.view.reset_cursor_style()
        self.view.switch_page(2)

    def onclick_next_from_page_2(self, widget: ui.Button) -> None:
        """'Next' button on the data specification page was clicked"""
        if not self.validate_data_specification_input():
            return
        if self.model.finished_steps == 1:
            self.model.finished_steps = 2
        self.view.show_notification(Notification.INFO, "Integrity checking page is still under construction")

    def onclick_previous_from_page_2(self, widget: ui.Button) -> None:
        """'Previous' button on the data specification page was clicked"""
        self.view.switch_page(1)
