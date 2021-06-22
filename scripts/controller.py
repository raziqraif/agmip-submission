from __future__ import annotations  # Delay the evaluation of undefined types
from pathlib import Path

import ipywidgets as ui

from .view import CSS, Delimiter, Notification


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
        if self.model.last_finished_step == current_finished_step:
            return
        self.model.last_finished_step = current_finished_step
        current_page_number = current_finished_step + 1
        self.view.switch_page(current_page_number, is_last_active_page=True)

    def validate_data_specification_input(self) -> bool:  # TODO: Should be moved to model
        """Return true if all input are entered correctly, and false if not"""
        is_valid = False
        try:
            if len(self.model.model_name) == 0:
                self.view.show_notification(Notification.WARNING, "Model name is empty")
            elif len(self.model.delimiter) == 0:
                self.view.show_notification(Notification.WARNING, "Delimiter is empty")
            elif len(self.model.lines_to_skip) == 0:
                self.view.show_notification(Notification.WARNING, "Initial number of lines to skip is empty")
            elif int(self.model.lines_to_skip) < 0:
                self.view.show_notification(
                    Notification.WARNING, "Number of lines cannot be negative"
                )
            elif len(self.model.assigned_scenario_column) == 0:
                self.view.show_notification(Notification.WARNING, "Scenario column is empty")
            elif len(self.model.assigned_region_column) == 0:
                self.view.show_notification(Notification.WARNING, "Region column is empty")
            elif len(self.model.assigned_variable_column) == 0:
                self.view.show_notification(Notification.WARNING, "Variable column is empty")
            elif len(self.model.assigned_item_column) == 0:
                self.view.show_notification(Notification.WARNING, "Item column is empty")
            elif len(self.model.assigned_unit_column) == 0:
                self.view.show_notification(Notification.WARNING, "Unit column is empty")
            elif len(self.model.assigned_year_column) == 0:
                self.view.show_notification(Notification.WARNING, "Year column is empty")
            elif len(self.model.assigned_value_column) == 0:
                self.view.show_notification(Notification.WARNING, "Value column is empty")
            elif (
                len(
                    set(
                        [
                            self.model.assigned_scenario_column,
                            self.model.assigned_region_column,
                            self.model.assigned_variable_column,
                            self.model.assigned_item_column,
                            self.model.assigned_unit_column,
                            self.model.assigned_year_column,
                            self.model.assigned_value_column,
                        ]
                    )
                )
                < 7  # If there are no duplicate assignment, we should have a set of 7 columns
            ):
                self.view.show_notification(
                    Notification.WARNING, "Output data has duplicate columns"
                )
            else:
                is_valid = True
        except ValueError:
            self.view.show_notification(Notification.WARNING, "Invalid number of lines")
        return is_valid

    def onchange_ua_file_label(self, change: dict) -> None:
        """Value of the hidden file label in upload area (ua) changed"""
        CSV = ".csv"
        file_name: str = change["new"]
        if len(file_name) == 0:  # This change was triggered by View's internal operation, not by a user aciton
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
        if self.model.last_finished_step == 0:
            self.model.last_finished_step = 1
            self.view.modify_cursor(CSS.CURSOR_MOD__WAIT)
            error_message = self.model.init_data_specification_states(self.model.uploaded_filename)
            self.view.update_data_specification_page()
            if error_message is not None:
                self.view.show_notification(Notification.ERROR, error_message)
            else:
                self.view.show_notification(Notification.INFO, Notification.FIELDS_WERE_PREPOPULATED)
            self.view.modify_cursor(None)
        self.view.switch_page(2)

    def onclick_next_from_page_2(self, widget: ui.Button) -> None:
        """'Next' button on the data specification page was clicked"""
        if not self.validate_data_specification_input():
            return
        if self.model.last_finished_step == 1:
            self.model.last_finished_step = 2
        self.view.show_notification(Notification.INFO, "Integrity checking page is still under construction")

    def onclick_previous_from_page_2(self, widget: ui.Button) -> None:
        """'Previous' button on the data specification page was clicked"""
        self.view.switch_page(1)

    def onchange_model_name_dropdown(self, change: dict) -> None:
        """The selection in 'model name' dropdown changed"""
        new_value = change["new"]
        # The event is triggered programmatically by page update, and not by dropdown selection
        if new_value == self.model.model_name:
            return
        self.model.model_name = new_value
        self.view.update_data_specification_page()

    def onchange_header_is_included_checkbox(self, change: dict) -> None:
        """The state of 'header is included' checkbox changed"""
        new_value = change["new"]
        # The event is triggered programmatically by page update, and not by checkbox selection
        if new_value == self.model.header_is_included:
            return
        self.model.header_is_included = new_value
        self.view.update_data_specification_page()

    def onchange_lines_to_skip_text(self, change: dict) -> None:
        """The content of 'lines to skip' text changed"""
        new_value = change["new"]
        try:
            new_value = int(new_value)
            # The event is triggered programmatically by page update, and not by a user action
            if new_value == self.model.lines_to_skip:
                return
            if new_value < 0:
                self.view.show_notification(Notification.WARNING, "Number of lines cannot be negative")
                new_value = 0
            self.model.lines_to_skip = new_value
        except:
            self.view.show_notification(Notification.WARNING, "Invalid number of lines")
            self.model.lines_to_skip = 0 
        self.view.update_data_specification_page()

    def onchange_delimiter_dropdown(self, change: dict) -> None:
        """The selection in 'delimiter' dropdown changed"""
        new_value = Delimiter.get_model(change["new"])
        # The event is triggered programmatically by page update, and not by dropdown selection
        if new_value == self.model.delimiter:
            return
        self.model.delimiter = new_value
        self.view.modify_cursor(CSS.CURSOR_MOD__PROGRESS)
        self.view.update_data_specification_page()
        self.view.modify_cursor(None)

    def onchange_scenarios_to_ignore_text(self, change: dict) -> None:
        """The content of 'scenarios to ignore' text changed"""
        new_value = change["new"]
        # The event is triggered programmatically by page update, and not by user actions
        if new_value == self.model.scenarios_to_ignore:
            return
        self.model.scenarios_to_ignore = new_value
        self.view.update_data_specification_page()

    def onchange_scenario_column_dropdown(self, change: dict) -> None:
        """The selection in 'scenario column' dropdown was changed"""
        new_value = change["new"]
        # The event is triggered programmatically by page update, instead of by a user action
        if new_value == self.model.assigned_scenario_column:
            return
        self.model.assigned_scenario_column = new_value
        self.view.update_data_specification_page()

    def onchange_region_column_dropdown(self, change: dict) -> None:
        """The selection in 'region column' dropdown changed"""
        new_value = change["new"]
        # The event is triggered programmatically by page update, instead of by a user action
        if new_value == self.model.assigned_region_column:
            return
        self.model.assigned_region_column = new_value
        self.view.update_data_specification_page()

    def onchange_variable_column_dropdown(self, change: dict) -> None:
        """The selection in 'variable column' dropdown changed"""
        new_value = change["new"]
        # The event is triggered programmatically by page update, instead of by a user action
        if new_value == self.model.assigned_variable_column:
            return
        self.model.assigned_variable_column = new_value
        self.view.update_data_specification_page()

    def onchange_item_column_dropdown(self, change: dict) -> None:
        """The selection in 'item column' dropdown changed"""
        new_value = change["new"]
        # The event is triggered programmatically by page update, instead of by a user action
        if new_value == self.model.assigned_item_column:
            return
        self.model.assigned_item_column = new_value
        self.view.update_data_specification_page()

    def onchange_unit_column_dropdown(self, change: dict) -> None:
        """The selection in 'unit column' dropdown changed"""
        new_value = change["new"]
        # The event is triggered programmatically by page update, instead of by a user action
        if new_value == self.model.assigned_unit_column:
            return
        self.model.assigned_unit_column = new_value
        self.view.update_data_specification_page()

    def onchange_year_column_dropdown(self, change: dict) -> None:
        """The selection in 'year column' dropdown changed"""
        new_value = change["new"]
        # The event is triggered programmatically by page update, instead of by a user action
        if new_value == self.model.assigned_year_column:
            return
        self.model.assigned_year_column = new_value
        self.view.update_data_specification_page()

    def onchange_value_column_dropdown(self, change: dict) -> None:
        """The selection in 'value column' dropdown changed"""
        new_value = change["new"]
        # The event is triggered programmatically by page update, instead of by a user action
        if new_value == self.model.assigned_value_column:
            return
        self.model.assigned_value_column = new_value
        self.view.update_data_specification_page()
