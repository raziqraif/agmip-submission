from __future__ import annotations  # Delay the evaluation of undefined types
from pathlib import Path

import ipywidgets as ui

from .namespaces import VisualizationTab
from .namespaces import Page
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

    def _reset_later_pages(self) -> None:
        """Set the current page as the last/furthest active page"""
        if self.model.furthest_active_page == self.model.current_page:
            return
        self.model.furthest_active_page = self.model.current_page
        self.view.update_app()

    def validate_data_specification_input(self) -> bool:  # TODO: Should be moved to model
        """Return true if all input are entered correctly, and false if not"""
        is_valid = False
        try:
            if len(self.model.model_name) == 0:
                self.view.show_notification(Notification.WARNING, "Model name is empty")
            elif len(self.model.delimiter) == 0:
                self.view.show_notification(Notification.WARNING, "Delimiter is empty")
            elif int(self.model.lines_to_skip) < 0:
                self.view.show_notification(Notification.WARNING, "Number of lines cannot be negative")
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
                self.view.show_notification(Notification.WARNING, "Output data has duplicate columns")
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
        self._reset_later_pages()

    def onclick_remove_file(self, widget: ui.Button) -> None:
        """'x' button in the file upload snackbar was clicked"""
        assert len(self.model.uploaded_filename) > 0
        self.model.remove_file(self.model.uploaded_filename)
        self.model.uploaded_filename = ""
        self.view.update_file_upload_page(None)
        self._reset_later_pages()

    def onclick_next_from_page_1(self, widget: ui.Button) -> None:
        """'Next' button on the file upload page was clicked"""
        if len(self.model.uploaded_filename) == 0:
            self.view.show_notification(Notification.INFO, Notification.PLEASE_UPLOAD)
            return
        self.view.modify_cursor(CSS.CURSOR_MOD__WAIT)
        if self.model.furthest_active_page == Page.FILE_UPLOAD:
            self.model.furthest_active_page = Page.DATA_SPECIFICATION
            error_message = self.model.init_data_specification_states(self.model.uploaded_filename)
            self.view.update_data_specification_page()
            if error_message is not None:
                self.view.show_notification(Notification.ERROR, error_message)
            else:
                self.view.show_notification(Notification.INFO, Notification.FIELDS_WERE_PREPOPULATED)
        self.model.current_page = Page.DATA_SPECIFICATION
        self.view.update_app()
        self.view.modify_cursor(None)

    def onclick_next_from_page_2(self, widget: ui.Button) -> None:
        """'Next' button on the data specification page was clicked"""
        if not self.validate_data_specification_input():
            return
        self.view.modify_cursor(CSS.CURSOR_MOD__WAIT)
        if self.model.furthest_active_page == Page.DATA_SPECIFICATION:
            self.model.furthest_active_page = Page.INTEGRITY_CHECKING
            self.model.init_integrity_checking_states(
                raw_csv=self.model.raw_csv_rows,
                delimiter=self.model.delimiter,
                header_is_included=self.model.header_is_included,
                lines_to_skip=self.model.lines_to_skip,
                scenarios_to_ignore=set(self.model.scenarios_to_ignore_str.split(",")),
                model_name=self.model.model_name,
                scenario_colnum=self.model._assigned_colnum_for_scenario,
                region_colnum=self.model._assigned_colnum_for_region,
                variable_colnum=self.model._assigned_colnum_for_variable,
                item_colnum=self.model._assigned_colnum_for_item,
                unit_colnum=self.model._assigned_colnum_for_unit,
                year_colnum=self.model._assigned_colnum_for_year,
                value_colnum=self.model._assigned_colnum_for_value,
            )
            self.view.update_integrity_checking_page()
        self.model.current_page = Page.INTEGRITY_CHECKING
        self.view.update_app()
        self.view.modify_cursor(None)

    def onclick_previous_from_page_2(self, widget: ui.Button) -> None:
        """'Previous' button on the data specification page was clicked"""
        self.model.current_page = Page.FILE_UPLOAD
        self.view.update_app()

    def onclick_next_from_page_3(self, widget: ui.Button) -> None:
        """'Next' button on the data specification page was clicked"""
        if self.model.furthest_active_page == Page.INTEGRITY_CHECKING:
            self.model.furthest_active_page = Page.PLAUSIBILITY_CHECKING
        # TODO: Perform data validation first
        self.model.current_page = Page.PLAUSIBILITY_CHECKING
        self.view.update_app()

    def onclick_previous_from_page_3(self, widget: ui.Button) -> None:
        """'Previous' button on the data specification page was clicked"""
        self.model.current_page = Page.DATA_SPECIFICATION
        self.view.update_app()

    def onchange_model_name_dropdown(self, change: dict) -> None:
        """The selection in 'model name' dropdown changed"""
        new_value = change["new"]
        # The event is triggered programmatically by page update, and not by dropdown selection
        if new_value == self.model.model_name:
            return
        self.model.model_name = new_value
        self.view.update_data_specification_page()
        self._reset_later_pages()

    def onchange_header_is_included_checkbox(self, change: dict) -> None:
        """The state of 'header is included' checkbox changed"""
        new_value = change["new"]
        # The event is triggered programmatically by page update, and not by checkbox selection
        if new_value == self.model.header_is_included:
            return
        self.model.header_is_included = new_value
        self.view.update_data_specification_page()
        self._reset_later_pages()

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
        self._reset_later_pages()

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
        self._reset_later_pages()

    def onchange_scenarios_to_ignore_text(self, change: dict) -> None:
        """The content of 'scenarios to ignore' text changed"""
        new_value = change["new"]
        # The event is triggered programmatically by page update, and not by user actions
        if new_value == self.model.scenarios_to_ignore_str:
            return
        self.model.scenarios_to_ignore_str = new_value
        self.view.update_data_specification_page()
        self._reset_later_pages()

    def onchange_scenario_column_dropdown(self, change: dict) -> None:
        """The selection in 'scenario column' dropdown was changed"""
        new_value = change["new"]
        # The event is triggered programmatically by page update, instead of by a user action
        if new_value == self.model.assigned_scenario_column:
            return
        self.model.assigned_scenario_column = new_value
        self.view.update_data_specification_page()
        self._reset_later_pages()

    def onchange_region_column_dropdown(self, change: dict) -> None:
        """The selection in 'region column' dropdown changed"""
        new_value = change["new"]
        # The event is triggered programmatically by page update, instead of by a user action
        if new_value == self.model.assigned_region_column:
            return
        self.model.assigned_region_column = new_value
        self.view.update_data_specification_page()
        self._reset_later_pages()

    def onchange_variable_column_dropdown(self, change: dict) -> None:
        """The selection in 'variable column' dropdown changed"""
        new_value = change["new"]
        # The event is triggered programmatically by page update, instead of by a user action
        if new_value == self.model.assigned_variable_column:
            return
        self.model.assigned_variable_column = new_value
        self.view.update_data_specification_page()
        self._reset_later_pages()

    def onchange_item_column_dropdown(self, change: dict) -> None:
        """The selection in 'item column' dropdown changed"""
        new_value = change["new"]
        # The event is triggered programmatically by page update, instead of by a user action
        if new_value == self.model.assigned_item_column:
            return
        self.model.assigned_item_column = new_value
        self.view.update_data_specification_page()
        self._reset_later_pages()

    def onchange_unit_column_dropdown(self, change: dict) -> None:
        """The selection in 'unit column' dropdown changed"""
        new_value = change["new"]
        # The event is triggered programmatically by page update, instead of by a user action
        if new_value == self.model.assigned_unit_column:
            return
        self.model.assigned_unit_column = new_value
        self.view.update_data_specification_page()
        self._reset_later_pages()

    def onchange_year_column_dropdown(self, change: dict) -> None:
        """The selection in 'year column' dropdown changed"""
        new_value = change["new"]
        # The event is triggered programmatically by page update, instead of by a user action
        if new_value == self.model.assigned_year_column:
            return
        self.model.assigned_year_column = new_value
        self.view.update_data_specification_page()
        self._reset_later_pages()

    def onchange_value_column_dropdown(self, change: dict) -> None:
        """The selection in 'value column' dropdown changed"""
        new_value = change["new"]
        # The event is triggered programmatically by page update, instead of by a user action
        if new_value == self.model.assigned_value_column:
            return
        self.model.assigned_value_column = new_value
        self.view.update_data_specification_page()
        self._reset_later_pages()

    def onclick_submit(self, widget: ui.Button) -> None:
        """The 'submit' button in the last page was clicked"""
        self.view.show_notification(Notification.INFO, "Submission feature is still in progress.")

    def onclick_previous_from_page_4(self, widget: ui.Button) -> None:
        """The 'submit' button in the last page was clicked"""
        self.model.current_page = Page.INTEGRITY_CHECKING
        self.view.update_app()

    def onclick_value_trends_tab(self, widget: ui.Button) -> None:
        """Value trends tab was clicked"""
        self.model.active_visualization_tab = VisualizationTab.VALUE_TRENDS
        self.view.update_plausibility_checking_page()

    def onclick_growth_trends_tab(self, widget: ui.Button) -> None:
        """Growth trends tab was clicked"""
        self.model.active_visualization_tab = VisualizationTab.GROWTH_TRENDS
        self.view.update_plausibility_checking_page()

    def onclick_box_plot_tab(self, widget: ui.Button) -> None:
        """Box plot tab was clicked"""
        self.model.active_visualization_tab = VisualizationTab.BOX_PLOT
        self.view.update_plausibility_checking_page()
