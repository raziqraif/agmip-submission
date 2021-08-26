from __future__ import annotations  # Delay the evaluation of undefined types
from matplotlib import pyplot as plt
from threading import Timer
from typing import Callable, Optional, Union, List, Tuple, Any

import ipywidgets as ui
import numpy as np
from IPython.core.display import Javascript, clear_output, display
from IPython.core.display import HTML
from pandas.core.frame import DataFrame
from pandas.core.groupby.generic import DataFrameGroupBy
from traitlets.config.application import ApplicationError

from .utils import ApplicationMode, CSS
from .utils import Delimiter
from .utils import JSAppModel
from .utils import Notification
from .utils import VisualizationTab


PLOT_HEIGHT = 11
PLOT_WIDTH = 5.5


def set_dropdown_options(widget: ui.Dropdown, options: Tuple | List, onchange_callback) -> None:
    """
    Utility function to reassign options without triggering onchange callback.
    The options will be sorted first.
    """
    widget.unobserve(onchange_callback, "value")
    widget.options = sorted(options)
    widget.value = None
    widget.observe(onchange_callback, "value")


class View:
    DATA_SPEC_PAGE_IS_BEING_UPDATED = (
        False  # to assert that a page update will not recursively trigger another page update
    )

    def __init__(self):
        # Import MVC classes here to prevent circular import problem
        from .controller import Controller
        from .model import Model

        # MVC objects self.model: Model
        self.model: Model = Model()
        self.ctrl: Controller = Controller()

        # Base app's widgets that need to be manipulated
        self.app_container: ui.Box
        self.app_title: ui.HTML
        self.app_header: ui.Box
        self.app_body: ui.Box
        self.user_mode_button: ui.Button
        self.user_page_stepper: ui.Box
        self.user_page_container: ui.Box
        self.user_mode_btn: ui.Button
        self.admin_mode_btn: ui.Button
        self.admin_page: ui.Box
        self.notification: ui.Box
        self._notification_timer: Timer = Timer(0.0, lambda x: None)
        # Admin page's widgets that need to be manipulated
        self.submissions_tbl: ui.HTML
        # File upload page's widgets that need to be manipulated
        self.ua_file_label: ui.Label  # ua here stands for "upload area"
        self.uploaded_file_name_box: ui.Box
        # Data specification page's widgets that need to be manipulated
        # - parsing widgets
        self.model_name_ddown: ui.Dropdown
        self.delimiter_ddown: ui.Dropdown
        self.header_is_included_chkbox: ui.Checkbox
        self.lines_to_skip_txt: ui.Text
        self.scenarios_to_ignore_txt: ui.Textarea
        # - column assignment widgets
        self.model_name_lbl: ui.Label
        self.scenario_column_ddown: ui.Dropdown
        self.region_column_ddown: ui.Dropdown
        self.variable_column_ddown: ui.Dropdown
        self.item_column_ddown: ui.Dropdown
        self.unit_column_ddown: ui.Dropdown
        self.year_column_ddown: ui.Dropdown
        self.value_column_ddown: ui.Dropdown
        # - preview tables
        self.input_data_preview_tbl: ui.GridBox
        self.output_data_preview_tbl: ui.GridBox
        self._input_data_table_childrenpool: list[ui.Box] = []
        # Integrity checking page's widgets that need to be manipulated
        self.duplicate_rows_lbl: ui.Label
        self.rows_w_struct_issues_lbl: ui.Label
        self.rows_w_ignored_scenario_lbl: ui.Label
        self.accepted_rows_lbl: ui.Label
        self.bad_labels_tbl: ui.HTML
        self.unknown_labels_tbl: ui.GridBox
        self._unknown_labels_tbl_cell_pool: list[ui.Box] = []
        # Plausibility checking page's widgets that need to be manipulated
        # - visualization tab elements & tab contents
        self.valuetrends_tabelement: ui.Box
        self.valuetrends_tabcontent: ui.Box
        self.growthtrends_tabelement: ui.Box
        self.growthtrends_tabcontent: ui.Box
        # - value trends visualization widgets
        self.valuetrends_scenario_ddown: ui.Dropdown
        self.valuetrends_region_ddown: ui.Dropdown
        self.valuetrends_variable_ddown: ui.Dropdown
        self.valuetrends_viz_output: ui.Output
        # - growth trends visualization widgets
        self.growthtrends_scenario_ddown: ui.Dropdown
        self.growthtrends_region_ddown: ui.Dropdown
        self.growthtrends_variable_ddown: ui.Dropdown
        self.growthtrends_viz_output: ui.Output

    def intro(self, model: Model, ctrl: Controller) -> None:  # type: ignore # noqa
        """Introduce MVC modules to each other"""
        self.model = model
        self.ctrl = ctrl

    def display(self) -> None:
        """Build and show notebook user interface"""
        self.app_container = self._build_app()
        # Display the appropriate html files and our ipywidgets app
        display(HTML(filename="style.html"))
        display(self.app_container)
        # Embed Javascript app model in Javascript context
        # TODO: Move the serialization data / functionality to Model and remove JSAppModel class (to reduce the amount of abstractions)
        javascript_model: JSAppModel = self.model.javascript_model
        display(HTML(f"<script> APP_MODEL = {javascript_model.serialize()}</script>"))
        display(HTML(filename="script.html"))

    def modify_cursor_style(self, new_cursor_mod_class: Optional[str]) -> None:
        """
        Change cursor style by assigning the passed CSS class to the app's DOM
        If None was passed, the cursor style will be reset
        """
        cursor_mod_classes = CSS.get_cursor_mod_classes()
        for cursor_mod_class in cursor_mod_classes:  # Remove all other cursor mods from DOM
            self.app_container.remove_class(cursor_mod_class)
        if new_cursor_mod_class is not None:
            assert new_cursor_mod_class in cursor_mod_classes
            self.app_container.add_class(new_cursor_mod_class)

    def show_notification(self, variant: str, content: str) -> None:
        """Display a notification to the user"""
        assert variant in Notification._VARIANTS
        # Cancel existing timer if it's still running
        self._notification_timer.cancel()
        # Reset the notification's DOM classes
        # This is important because we implement a clickaway listener in JS which removes a DOM class from the
        # notification's view without notifying the notification's model. So, we want to make sure that the DOM classes
        # maintained in both view and model are synchronized. (The view and model in this context refers to ipywidgets'
        # view and model)
        self.notification._dom_classes = (CSS.NOTIFICATION,)
        # Update notification content
        notification_text = self.notification.children[1]
        assert isinstance(notification_text, ui.Label)
        notification_text.value = content
        # Update notification visibility & style
        if variant == Notification.SUCCESS:
            self.notification.children = (Notification.SUCCESS_ICON, notification_text)
            self.notification._dom_classes = (CSS.NOTIFICATION, CSS.NOTIFICATION__SHOW, CSS.NOTIFICATION__SUCCESS)
            notification_text._dom_classes = (CSS.COLOR_MOD__WHITE,)
        elif variant == Notification.INFO:
            self.notification.children = (Notification.INFO_ICON, notification_text)
            self.notification._dom_classes = (CSS.NOTIFICATION, CSS.NOTIFICATION__SHOW, CSS.NOTIFICATION__INFO)
            notification_text._dom_classes = (CSS.COLOR_MOD__WHITE,)
        elif variant == Notification.WARNING:
            self.notification.children = (Notification.WARNING_ICON, notification_text)
            self.notification._dom_classes = (CSS.NOTIFICATION, CSS.NOTIFICATION__SHOW, CSS.NOTIFICATION__WARNING)
            notification_text._dom_classes = (CSS.COLOR_MOD__BLACK,)
        elif variant == Notification.ERROR:
            self.notification.children = (Notification.ERROR_ICON, notification_text)
            self.notification._dom_classes = (CSS.NOTIFICATION, CSS.NOTIFICATION__SHOW, CSS.NOTIFICATION__ERROR)
            notification_text._dom_classes = (CSS.COLOR_MOD__WHITE,)
        else:
            assert len("Variant does not exists") == 0
        # Create a timer to hide notification after X seconds
        self._notification_timer = Timer(3.5, self.notification.remove_class, args=[CSS.NOTIFICATION__SHOW])
        self._notification_timer.start()

    def show_modal_dialog(self, title: str, body: str) -> None:
        """
        Show modal dialog
        NOTE: The current method to display a modal dialog requires the title/body argument to not have a newline
        """
        data = """
            require(
                ["base/js/dialog"],
                function(dialog) {
                    dialog.modal({
                        title: '%s',
                        body: '%s',
                        sanitize: false,
                        buttons: {
                            'Close': {}
                        }
                });
            })
            """ % (
            title,
            body,
        )
        display(Javascript(data=data, css="modal.css"))

    def update_base_app(self) -> None:
        """Update the base app"""
        # Create helper variables
        NUM_OF_PAGES = len(self.user_page_container.children)
        assert self.model.current_user_page > 0 and self.model.current_user_page <= NUM_OF_PAGES
        assert self.model.furthest_active_user_page > 0 and self.model.furthest_active_user_page <= NUM_OF_PAGES
        current_page_index = self.model.current_user_page - 1
        # Update visibility of pages and style of page stepper elements
        for page_index in range(0, NUM_OF_PAGES):
            # Get page and stepper element
            page = self.user_page_container.children[page_index]
            stepper_element = self.user_page_stepper.children[page_index]
            assert isinstance(page, ui.Box)
            assert isinstance(stepper_element, ui.Box)
            if page_index == current_page_index:
                # Show the page and style the stepper element apropriately
                page.remove_class(CSS.DISPLAY_MOD__NONE)
                stepper_element._dom_classes = (CSS.STEPPER_EL, CSS.STEPPER_EL__CURRENT)
            else:
                # Hide the page and style the stepper element appropriately
                page.add_class(CSS.DISPLAY_MOD__NONE)
                stepper_element._dom_classes = (
                    (CSS.STEPPER_EL, CSS.STEPPER_EL__ACTIVE)
                    if page_index < self.model.furthest_active_user_page
                    else (CSS.STEPPER_EL, CSS.STEPPER_EL__INACTIVE)
                )
        # Update application mode
        if self.model.application_mode == ApplicationMode.USER:
            self.app_header.children = [self.app_title, self.user_mode_btn]
            self.user_page_container.remove_class(CSS.DISPLAY_MOD__NONE)
            self.user_page_stepper.remove_class(CSS.DISPLAY_MOD__NONE)
            self.app_body.children = [self.user_page_stepper, self.user_page_container]
        if self.model.application_mode == ApplicationMode.ADMIN:
            self.app_header.children = [self.app_title, self.admin_mode_btn]
            self.user_page_container.add_class(CSS.DISPLAY_MOD__NONE)
            self.user_page_stepper.add_class(CSS.DISPLAY_MOD__NONE)
            table_rows = ""
            cur_len = 0
            for row in self.model.get_submitted_files_info():
                table_rows += "<tr>"
                for colidx in range(len(row)):
                    field = row[colidx]
                    table_rows += f"<td>{field}</td>"
                table_rows += "</tr>"
                cur_len += 1
            for _ in range(cur_len, 15):
                table_rows += "<tr><td>-</td><td>-</td><td>-</td></tr>"
            self.submissions_tbl.value = f"""
                <table class="table">
                    <thead>
                        <th style="width: 350px;">File</th>
                        <th style="width: 200px;">Associated Project</th>
                        <th style="width: 150px;">Status</th>
                    </thead>
                    <tbody>
                        {table_rows}
                    </tbody>
                </table>
            """

            # NOTE: It is important for us to NOT remove user pages from DOM tree even when going into admin mode. Else,
            # the event handler registration that we do in the Javascript context (e.g. for file upload) will no longer work
            self.app_body.children = [self.user_page_stepper, self.user_page_container, self.admin_page]

    def update_file_upload_page(self) -> None:
        """Update the file upload page"""
        # Update the file name snackbar
        children_: Tuple[ui.HTML, ui.Box] = self.uploaded_file_name_box.children
        no_file_uploaded_widget = children_[0]
        file_uploaded_widget = children_[1]
        if self.model.uploadedfile_name != "":
            # Show "No file was uploaded"
            no_file_uploaded_widget.add_class(CSS.DISPLAY_MOD__NONE)
            file_uploaded_widget.remove_class(CSS.DISPLAY_MOD__NONE)
            children: tuple[ui.Label, ui.Button] = file_uploaded_widget.children
            label_widget = children[0]
            label_widget.value = self.model.uploadedfile_name
        else:
            # Show the name of the uploaded file
            file_uploaded_widget.add_class(CSS.DISPLAY_MOD__NONE)
            no_file_uploaded_widget.remove_class(CSS.DISPLAY_MOD__NONE)
        # Reset the hidden filename value
        self.ua_file_label.value = ""

    def update_data_specification_page(self):
        """Update the state of data specification page"""
        assert self.DATA_SPEC_PAGE_IS_BEING_UPDATED != True
        self.DATA_SPEC_PAGE_IS_BEING_UPDATED = True
        # Update input format specification widgets
        set_dropdown_options(
            self.model_name_ddown, ("", *self.model.VALID_MODEL_NAMES), self.ctrl.onchange_model_name_dropdown
        )
        self.model_name_ddown.value = self.model.model_name
        set_dropdown_options(self.delimiter_ddown, ("", *Delimiter.get_views()), self.ctrl.onchange_delimiter_dropdown)
        self.delimiter_ddown.value = Delimiter.get_view(self.model.delimiter)
        self.header_is_included_chkbox.value = self.model.header_is_included
        self.lines_to_skip_txt.value = str(self.model.lines_to_skip)
        self.scenarios_to_ignore_txt.value = self.model.scenarios_to_ignore_str
        # Update column assignment widgets
        column_options = ("", *self.model.column_assignment_options)
        self.model_name_lbl.value = self.model.model_name if len(self.model.model_name) > 0 else "<Model Name>"
        set_dropdown_options(self.scenario_column_ddown, column_options, self.ctrl.onchange_scenario_column_dropdown)
        self.scenario_column_ddown.value = self.model.assigned_scenario_column
        set_dropdown_options(self.region_column_ddown, column_options, self.ctrl.onchange_region_column_dropdown)
        self.region_column_ddown.value = self.model.assigned_region_column
        set_dropdown_options(self.variable_column_ddown, column_options, self.ctrl.onchange_variable_column_dropdown)
        self.variable_column_ddown.value = self.model.assigned_variable_column
        set_dropdown_options(self.item_column_ddown, column_options, self.ctrl.onchange_item_column_dropdown)
        self.item_column_ddown.value = self.model.assigned_item_column
        set_dropdown_options(self.unit_column_ddown, column_options, self.ctrl.onchange_unit_column_dropdown)
        self.unit_column_ddown.value = self.model.assigned_unit_column
        set_dropdown_options(self.year_column_ddown, column_options, self.ctrl.onchange_year_column_dropdown)
        self.year_column_ddown.value = self.model.assigned_year_column
        set_dropdown_options(self.value_column_ddown, column_options, self.ctrl.onchange_value_column_dropdown)
        self.value_column_ddown.value = self.model.assigned_value_column
        # Upload the input data preview table
        # TODO: implement this table with an ipywidgets HTML
        table_content = self.model.input_data_preview_content
        number_of_columns = table_content.shape[1]
        table_content = table_content.flatten()
        # - increase pool size if it's insufficient
        if len(table_content) > len(self._input_data_table_childrenpool):
            pool_addition = [ui.Box(children=[ui.Label(value="")]) for _ in range(len(table_content))]
            self._input_data_table_childrenpool += pool_addition
        content_index = 0
        assert self._input_data_table_childrenpool is not None
        for content in table_content:
            content_box = self._input_data_table_childrenpool[content_index]
            assert isinstance(content_box, ui.Box)
            content_label = content_box.children[0]
            assert isinstance(content_label, ui.Label)
            content_label.value = content
            content_index += 1
        self.input_data_preview_tbl.children = self._input_data_table_childrenpool[: table_content.size]
        self.input_data_preview_tbl.layout.grid_template_columns = f"repeat({number_of_columns}, 1fr)"
        # Update the output the data preview table
        # TODO: implement this table with an ipywidgets HTML instead of GridBox
        table_content = self.model.output_data_preview_content
        table_content = table_content.flatten()
        assert table_content.size == len(self.output_data_preview_tbl.children)
        content_index = 0
        for content in table_content:
            content_box = self.output_data_preview_tbl.children[content_index]
            assert isinstance(content_box, ui.Box)
            content_label = content_box.children[0]
            assert isinstance(content_label, ui.Label)
            content_label.value = table_content[content_index]
            content_index += 1
        self.DATA_SPEC_PAGE_IS_BEING_UPDATED = False

    def update_integrity_checking_page(self) -> None:
        """Update the integrity checking page"""
        # Update the row summary labels
        self.rows_w_struct_issues_lbl.value = "{:,}".format(self.model.nrows_w_struct_issue)
        self.rows_w_ignored_scenario_lbl.value = "{:,}".format(self.model.nrows_w_ignored_scenario)
        self.duplicate_rows_lbl.value = "{:,}".format(self.model.nrows_duplicates)
        self.accepted_rows_lbl.value = "{:,}".format(self.model.nrows_accepted)
        # Update the bad labels overview table
        _table_rows = ""
        for row in self.model.bad_labels_overview_tbl:
            _table_rows += "<tr>"
            for colidx in range(len(row)):
                field = row[colidx]
                if colidx == 1:  # If middle field / "Associated column" field
                    _table_rows += f"<td>{field}</td>"
                else:
                    _table_rows += f'<td title="{field}">{field}</td>'
            _table_rows += "</tr>"
        self.bad_labels_tbl.value = f"""
            <table>
                <thead>
                    <th>Label</th>
                    <th>Associated column</th>
                    <th>Fix</th>
                </thead>
                <tbody>
                    {_table_rows}
                </tbody>
            </table>
            """
        self._update_unknown_labels_overview_table()

    def _update_unknown_labels_overview_table(self) -> None:
        """
        Update the unknown labels overview table
        Refer to the documentation surrounding the initialization of this table to understand how it was built
        and how it needs to be updated. @date Aug 3, 2021
        """
        # Calculate helper variables
        NCOLS = 5
        nrowsneeded = len(self.model.unknown_labels_overview_tbl)
        nrowssupported = int(  # We deduct NCOLS from the calculation to exclude the header row
            (len(self._unknown_labels_tbl_cell_pool) - NCOLS) / NCOLS
        )
        # Enlarge the children pool if needed
        if nrowsneeded > nrowssupported:
            # Create enough child cells to form the missing rows
            # Note: each row in this table is in the form of [label, label, label, dropdown, checkbox]
            for row_index in range(nrowssupported, nrowsneeded):
                # create a lambda that returns an onchange callback that can be assigned to ipywidgets dropdown
                _get_dropdown_callback = lambda row_index: lambda change: self.ctrl.onchange_fix_dropdown(
                    change, row_index
                )
                # create a lambda returns an onchange callback that can be assigned to ipywidgets checkbox
                _get_checkbox_callback = lambda row_index: lambda change: self.ctrl.onchange_override_checkbox(
                    change, row_index
                )
                dropdown = ui.Dropdown()
                dropdown.observe(_get_dropdown_callback(row_index), "value")
                checkbox = ui.Checkbox(indent=False, value=False, description="")
                checkbox.observe(_get_checkbox_callback(row_index), "value")
                self._unknown_labels_tbl_cell_pool += [
                    ui.Box(children=[ui.HTML(value="-")]),
                    ui.Box(children=[ui.HTML(value="-")]),
                    ui.Box(children=[ui.HTML(value="-")]),
                    ui.Box(children=[dropdown]),
                    ui.Box(children=[checkbox]),
                ]
        # Update the values being displayed at each row
        for row_index in range(nrowsneeded):
            # Get the cell widgets for this row
            cellpoolstartindex = (row_index * NCOLS) + NCOLS  #  we add NCOLS to account for header row
            unknownlabel_w, associatedcolumn_w, closestmatch_w, fix_w, override_w = [
                cell_wrapper.children[0]
                for cell_wrapper in self._unknown_labels_tbl_cell_pool[cellpoolstartindex : cellpoolstartindex + 5]
            ]
            assert isinstance(unknownlabel_w, ui.HTML)
            assert isinstance(associatedcolumn_w, ui.HTML)
            assert isinstance(closestmatch_w, ui.HTML)
            assert isinstance(fix_w, ui.Dropdown)
            assert isinstance(override_w, ui.Checkbox)
            # Get the cell values for this row from model
            row = self.model.unknown_labels_overview_tbl[row_index]
            unknownlabel, associatedcolumn, closestmatch, fix, override = row
            assert isinstance(unknownlabel, str)
            assert isinstance(associatedcolumn, str)
            assert isinstance(closestmatch, str)
            assert isinstance(fix, str)
            assert isinstance(override, bool)
            # Update cell widgets based on the retrieved values from model
            get_hoverable_html = lambda value: f"<span title={value}>{value}</span>"
            unknownlabel_w.value = get_hoverable_html(unknownlabel)
            associatedcolumn_w.value = associatedcolumn
            closestmatch_w.value = get_hoverable_html(closestmatch)
            fix_w.value = None
            if associatedcolumn == "-":
                fix_w.options = [""]
            elif associatedcolumn == "Scenario":
                fix_w.options = ["", *self.model.VALID_SCENARIOS]
            elif associatedcolumn == "Region":
                fix_w.options = ["", *self.model.VALID_REGIONS]
            elif associatedcolumn == "Variable":
                fix_w.options = ["", *self.model.VALID_VARIABLES]
            elif associatedcolumn == "Item":
                fix_w.options = ["", *self.model.VALID_ITEMS]
            elif associatedcolumn == "Unit":
                fix_w.options = ["", *self.model.VALID_UNITS]
            else:
                raise Exception("Unexpected associated column")
            fix_w.value = fix
            override_w.value = override
        # Assign the required rows to the table
        self.unknown_labels_tbl.children = self._unknown_labels_tbl_cell_pool[: (nrowsneeded + 1) * 5]

    def update_plausibility_checking_page(self) -> None:
        """Update the plausibility checking page"""
        # Update the style and visibility of tab elements and tab content
        is_active: Callable[[VisualizationTab], bool] = lambda tab: self.model.active_visualization_tab == tab
        # - update the style and visibility of value trends tab element & content
        if is_active(VisualizationTab.VALUE_TRENDS):
            self.valuetrends_tabelement.add_class(CSS.VISUALIZATION_TAB__ELEMENT__ACTIVE)
            self.valuetrends_tabcontent.remove_class(CSS.DISPLAY_MOD__NONE)
        else:
            self.valuetrends_tabelement.remove_class(CSS.VISUALIZATION_TAB__ELEMENT__ACTIVE)
            self.valuetrends_tabcontent.add_class(CSS.DISPLAY_MOD__NONE)
        # - update the style & visibility of growth trends tab element & content
        if is_active(VisualizationTab.GROWTH_TRENDS):
            self.growthtrends_tabelement.add_class(CSS.VISUALIZATION_TAB__ELEMENT__ACTIVE)
            self.growthtrends_tabcontent.remove_class(CSS.DISPLAY_MOD__NONE)
        else:
            self.growthtrends_tabelement.remove_class(CSS.VISUALIZATION_TAB__ELEMENT__ACTIVE)
            self.growthtrends_tabcontent.add_class(CSS.DISPLAY_MOD__NONE)
        # Update the dropdown options and values in the value trends tab
        # - scenario dropdown
        set_dropdown_options(
            self.valuetrends_scenario_ddown, self.model.uploaded_scenarios, self.ctrl.onchange_valuetrends_scenario
        )
        self.valuetrends_scenario_ddown.value = self.model.valuetrends_scenario
        # - region dropdown
        set_dropdown_options(
            self.valuetrends_region_ddown, self.model.uploaded_regions, self.ctrl.onchange_valuetrends_region
        )
        self.valuetrends_region_ddown.value = self.model.valuetrends_region
        # - variable dropdown
        set_dropdown_options(
            self.valuetrends_variable_ddown, self.model.uploaded_variables, self.ctrl.onchange_valuetrends_variable
        )
        self.valuetrends_variable_ddown.value = self.model.valuetrends_variable
        # Update the dropdown options and values in the growth trends tab
        # - scenario dropdown
        set_dropdown_options(
            self.growthtrends_scenario_ddown, self.model.uploaded_scenarios, self.ctrl.onchange_growthtrends_scenario
        )
        self.growthtrends_scenario_ddown.value = self.model.growthtrends_scenario
        # - region dropdown
        set_dropdown_options(
            self.growthtrends_region_ddown, self.model.uploaded_regions, self.ctrl.onchange_growthtrends_region
        )
        self.growthtrends_region_ddown.value = self.model.growthtrends_region
        # - variable dropdown
        set_dropdown_options(
            self.growthtrends_variable_ddown, self.model.uploaded_variables, self.ctrl.onchange_growthtrends_variable
        )
        self.growthtrends_variable_ddown.value = self.model.growthtrends_variable

    def update_value_trends_chart(self) -> None:
        """Visualize value trends"""
        # TODO: Fix legends possitioning issue
        with self.valuetrends_viz_output:
            clear_output(wait=True)
            _, axes = plt.subplots(figsize=(PLOT_HEIGHT, PLOT_WIDTH))  # size in inches
            if self.model.valuetrends_table is not None:
                # Make sure we have enough colors for all lines
                # https://stackoverflow.com/a/35971096/16133077
                num_plots = self.model.valuetrends_table.ngroups
                axes.set_prop_cycle(plt.cycler("color", plt.cm.jet(np.linspace(0, 1, num_plots))))  # type: ignore
                # Multi-line chart
                # https://stackoverflow.com/questions/29233283/plotting-multiple-lines-in-different-colors-with-pandas-dataframe?answertab=votes#tab-top
                for key, group in self.model.valuetrends_table:
                    axes = group.plot(
                        ax=axes,
                        kind="line",
                        x=self.model.valuetrends_table_year_colname,
                        y=self.model.valuetrends_table_value_colname,
                        label=key,
                    )
            axes.set_xlabel("Year")
            axes.set_ylabel("Value")
            plt.title("Value Trends")
            plt.grid()
            plt.show()

    def update_growth_trends_chart(self) -> None:
        """Visualize growth trends"""
        # TODO: Fix legends possitioning issue
        with self.growthtrends_viz_output:
            clear_output(wait=True)
            _, axes = plt.subplots(figsize=(PLOT_HEIGHT, PLOT_WIDTH))  # size in inches
            if self.model.growthtrends_table is not None:
                # Make sure we have enough colors for all lines
                # https://stackoverflow.com/a/35971096/16133077
                num_plots = self.model.growthtrends_table.ngroups
                axes.set_prop_cycle(plt.cycler("color", plt.cm.jet(np.linspace(0, 1, num_plots))))  # type: ignore
                # Multi-line chart
                # https://stackoverflow.com/questions/29233283/plotting-multiple-lines-in-different-colors-with-pandas-dataframe?answertab=votes#tab-top
                for key, group in self.model.growthtrends_table:
                    assert isinstance(group, DataFrame)
                    axes = group.plot(
                        ax=axes,
                        kind="line",
                        x=self.model.growthtrends_table_year_colname,
                        y=self.model.growthtrends_table_value_colname,
                        label=key,
                    )
            axes.set_xlabel("Year")
            axes.set_ylabel("Growth Value")
            plt.title("Growth Rate Trends")
            plt.grid()
            plt.show()

    def _build_app(self) -> ui.Box:
        """Build the application"""
        # Constants
        APP_TITLE = "AgMIP GlobalEcon Data Submission"
        # Create notification widget
        # TODO: Make notification text an attribute
        notification_text = ui.Label(value="")
        self.notification = ui.HBox(children=(Notification.SUCCESS_ICON, notification_text))
        self.notification.add_class(CSS.NOTIFICATION)
        # Create user mode widgets
        # - create stepper widget
        PAGE_TITLES = ["File Upload", "Data Specification", "Integrity Checking", "Plausibility Checking"]
        NUM_OF_PAGES = len(PAGE_TITLES)
        stepper_children = []
        for page_index in range(0, NUM_OF_PAGES):
            stepper_element_number = ui.HTML(value=str(page_index + 1))
            stepper_element_number.add_class(CSS.STEPPER_EL__NUMBER)
            stepper_element_title = ui.Label(value=PAGE_TITLES[page_index])
            stepper_element_title.add_class(CSS.STEPPER_EL__TITLE)
            stepper_element_separator = ui.HTML(value="<hr width=48px/>")
            stepper_element_separator.add_class(CSS.STEPPER_EL__SEPARATOR)
            stepper_element = (
                ui.Box(children=[stepper_element_number, stepper_element_title])
                if page_index == 0
                else ui.Box(children=[stepper_element_separator, stepper_element_number, stepper_element_title])
            )
            stepper_element.add_class(CSS.STEPPER_EL)
            stepper_element.add_class(CSS.STEPPER_EL__CURRENT if page_index == 0 else CSS.STEPPER_EL__INACTIVE)
            stepper_children.append(stepper_element)
        self.user_page_stepper = ui.HBox(children=stepper_children)
        # - create user pages & user page container
        self.user_page_container = ui.Box(
            children=[
                self._build_file_upload_page(),
                self._build_data_specification_page(),
                self._build_integrity_checking_page(),
                self._build_plausibility_checking_page(),
            ],
            layout=ui.Layout(flex="1", width="100%"),  # page container stores the current page
        )
        for page in self.user_page_container.children[1:]:  # hide all pages, except for the first one
            page.add_class(CSS.DISPLAY_MOD__NONE)
        # Create admin mode widgets
        self.admin_page = self._build_admin_page()
        # Create app header
        self.user_mode_btn = ui.Button(description="User Mode")
        self.user_mode_btn.on_click(self.ctrl.onclick_user_mode_btn)
        self.admin_mode_btn = ui.Button(description="Admin Mode")
        self.admin_mode_btn.on_click(self.ctrl.onclick_admin_mode_btn)
        self.app_title = ui.HTML(value=APP_TITLE)
        self.app_header = ui.Box(children=[self.app_title, self.user_mode_btn])
        self.app_header.add_class(CSS.HEADER_BAR)
        # Create app body
        self.app_body = ui.VBox(  # vbox for app body
            children=[self.user_page_stepper, self.user_page_container],  # - page stepper, page container
            layout=ui.Layout(flex="1", align_items="center", padding="36px 48px"),
        )
        # Create the app
        app = ui.VBox(  # vbox for app container
            children=[
                self.notification,  # - notification
                self.app_header,  # - app header bar
                self.app_body,  # - app body
            ],
        )
        app.add_class(CSS.APP)
        return app

    def _build_file_upload_page(self) -> ui.Box:
        """Build the file upload page"""
        # Create the upload area component (or ua for short)
        # - create the hidden file label
        # - upon successful upload, our Javascript code will notify the backend code the name of the uploaded file by
        # - modifying the value of this label widget    @ Aug 3, 2021
        self.ua_file_label = ui.Label(value="")
        self.ua_file_label.add_class(CSS.UA__FILE_LABEL)
        self.ua_file_label.observe(self.ctrl.onchange_ua_file_label, "value")
        # - remember the model id of hidden file label
        # - we will later inject this model id into the Javascript context, so that our Javascript code can find
        # - and manipulate the value of this hidden label  @ Aug 3, 2021
        # TODO: Remove the JSAppModel class and move its functionality to Model (to reduce the amount of abstractions)
        javascript_model = self.model.javascript_model
        javascript_model.ua_file_label_model_id = self.ua_file_label.model_id
        # - create a box representing the upload area component
        upload_area = ui.Box(  # box representing the upload area component
            children=[
                CSS.assign_class(
                    ui.HBox(  # - hbox for the component's background widgets
                        children=[
                            ui.HTML(  # -- first half of the upload instruction
                                value=f"""<strong class="{CSS.COLOR_MOD__BLUE}"">&#128206;&nbsp;
                                Add a CSV file&nbsp;</strong>"""
                            ),
                            ui.HTML(  # -- second half of the upload instruction
                                value=f'<div class="{CSS.COLOR_MOD__GREY}"">from your computer</div>'
                            ),
                        ]
                    ),
                    CSS.UA__BACKGROUND,
                ),
                ui.HTML(  # - invisible file uploader (HTML input[type="file"])
                    # NOTE: this widget will be targeted from the Javascript context by using the CSS class name,
                    # so do not remove the CSS class assignment
                    value=f"""
                    <input class="{CSS.UA__FILE_UPLOADER}" type="file" title="Click to browse" accept=".csv">
                    """
                ),
                self.ua_file_label,  # - hidden file label
            ],
            layout=ui.Layout(margin="20px 0px"),
        )
        upload_area.add_class(CSS.UA)
        # Create uploaded filename snackbar
        # TODO: improve the logic for this snackbar display management
        # - create a "snackbar" to show that no file has been uploaded
        no_file_uploaded = ui.HTML(
            value=(
                '<div style="width: 500px; line-height: 36px; text-align: center; background: rgba(75, 85, 99, 0.1);'
                ' color: var(--grey);"> No file uploaded </div>'
            )
        )
        # - create a snackbar to show the uploaded file's name
        uploaded_file_name = ui.Label(value="")
        x_button = ui.Button(icon="times")
        x_button.on_click(self.ctrl.onclick_remove_file)
        uploaded_file_snackbar = ui.Box(
            children=[
                uploaded_file_name,
                x_button,
            ],
        )
        uploaded_file_snackbar.add_class(CSS.FILENAME_SNACKBAR)
        uploaded_file_snackbar.add_class(CSS.DISPLAY_MOD__NONE)
        # - create the box
        self.uploaded_file_name_box = ui.Box(children=[no_file_uploaded, uploaded_file_snackbar])
        self.uploaded_file_name_box.layout = ui.Layout(margin="0px 0px 24px 0px")
        # Create project selection widget
        # TODO: change this to only allow single selection
        associatedprojects_select = ui.SelectMultiple(options=self.model.USER_GLOBALECON_PROJECTS)
        associatedprojects_select.observe(self.ctrl.onchange_associated_projects, "value")
        associatedprojects_select.layout = ui.Layout(margin="20px 0px 0px 0px", width="500px")
        associatedprojects_select.add_class(CSS.ASSOCIATED_PROJECT_SELECT)
        # Create navigation button
        next_button = ui.Button(description="Next", layout=ui.Layout(align_self="flex-end", justify_self="flex-end"))
        next_button.on_click(self.ctrl.onclick_next_from_upage_1)
        # Create the page
        return ui.VBox(  # vbox for page
            children=[
                ui.VBox(  # - vbox for the page's main components
                    children=[
                        ui.HBox(  # -- hbox for file upload instruction & info download button
                            children=[
                                ui.HTML(  # --- file upload instruction
                                    value='<h4 style="margin: 0px;">1) Upload a data file</h4>'
                                ),
                                ui.HTML(  # --- info download button
                                    value=f"""
                                    <a
                                        href="{str(self.model.INFOFILE_PATH)}" 
                                        download="{str(self.model.INFOFILE_PATH.name)}"
                                        class="{CSS.ICON_BUTTON}"
                                        style="line-height:16px; height:16px"
                                        title="Download info file"
                                    >
                                        <i class="fa fa-download"></i>
                                    </a>
                                    """
                                ),
                            ],
                            layout=ui.Layout(width="500px", align_items="flex-end"),
                        ),
                        upload_area,  # -- upload area
                        self.uploaded_file_name_box,  # -- uploaded file name box
                        ui.HTML(  # -- project selection instruction
                            value='<h4 style="margin: 0px;">2) Select associated projects</h4>'
                        ),
                        associatedprojects_select,  # -- project selection widget
                    ],
                    layout=ui.Layout(flex="1", justify_content="center"),
                ),
                ui.HBox(children=[next_button], layout=ui.Layout(align_self="flex-end")),  # -navigation button box
            ],
            layout=ui.Layout(flex="1", width="100%", align_items="center", justify_content="center"),
        )

    def _build_data_specification_page(self) -> ui.Box:
        """Build the data specification page"""
        # Create control widgets
        # - create control widgets for the input format specification section
        _control_layout = ui.Layout(flex="1 1", max_width="100%")
        self.model_name_ddown = ui.Dropdown(value="", options=[""], layout=_control_layout)
        self.model_name_ddown.observe(self.ctrl.onchange_model_name_dropdown, "value")
        self.header_is_included_chkbox = ui.Checkbox(indent=False, value=False, description="", layout=_control_layout)
        self.header_is_included_chkbox.observe(self.ctrl.onchange_header_is_included_checkbox, "value")
        self.lines_to_skip_txt = ui.Text(layout=_control_layout, continuous_update=False)
        self.lines_to_skip_txt.observe(self.ctrl.onchange_lines_to_skip_text, "value")
        self.delimiter_ddown = ui.Dropdown(value="", options=[""], layout=_control_layout)
        self.delimiter_ddown.observe(self.ctrl.onchange_delimiter_dropdown, "value")
        self.scenarios_to_ignore_txt = ui.Textarea(
            placeholder="(Optional) Enter comma-separated scenario values",
            layout=ui.Layout(flex="1", height="72px"),
            continuous_update=False,
        )
        self.scenarios_to_ignore_txt.observe(self.ctrl.onchange_scenarios_to_ignore_text, "value")
        # - create control widgets for the column assignment section
        self.model_name_lbl = ui.Label(value="")
        self.scenario_column_ddown = ui.Dropdown(value="", options=[""], layout=_control_layout)
        self.scenario_column_ddown.observe(self.ctrl.onchange_scenario_column_dropdown, "value")
        self.region_column_ddown = ui.Dropdown(value="", options=[""], layout=_control_layout)
        self.region_column_ddown.observe(self.ctrl.onchange_region_column_dropdown, "value")
        self.variable_column_ddown = ui.Dropdown(value="", options=[""], layout=_control_layout)
        self.variable_column_ddown.observe(self.ctrl.onchange_variable_column_dropdown, "value")
        self.item_column_ddown = ui.Dropdown(value="", options=[""], layout=_control_layout)
        self.item_column_ddown.observe(self.ctrl.onchange_item_column_dropdown, "value")
        self.unit_column_ddown = ui.Dropdown(value="", options=[""], layout=_control_layout)
        self.unit_column_ddown.observe(self.ctrl.onchange_unit_column_dropdown, "value")
        self.year_column_ddown = ui.Dropdown(value="", options=[""], layout=_control_layout)
        self.year_column_ddown.observe(self.ctrl.onchange_year_column_dropdown, "value")
        self.value_column_ddown = ui.Dropdown(value="", options=[""], layout=_control_layout)
        self.value_column_ddown.observe(self.ctrl.onchange_value_column_dropdown, "value")
        # - create the input data preview table
        # - TODO: implement this table with ipywidgets HTML
        self._input_data_table_childrenpool = [
            ui.Box(children=[ui.Label(value="")]) for _ in range(33)  # Using 33 as cache size is random
        ]
        self.input_data_preview_tbl = ui.GridBox(
            children=self._input_data_table_childrenpool[:24],  # 24 because we assume the table dimension to be
            # 3 x 8 (the row number will stay the same, but the column number may vary)
            layout=ui.Layout(grid_template_columns="repeat(8, 1fr)"),
        )
        self.input_data_preview_tbl.add_class(CSS.PREVIEW_TABLE)
        # - create the output data preview table
        # - TODO: implement this table with ipywidgets HTML
        self.output_data_preview_tbl = ui.GridBox(
            children=[
                ui.Box(children=[ui.Label(value="")]) for _ in range(24)
            ],  # 24 because of the 3 x 8 table dimension (invariant)
            layout=ui.Layout(grid_template_columns="repeat(8, 1fr"),
        )
        self.output_data_preview_tbl.add_class(CSS.PREVIEW_TABLE)
        # - create control widgets for page navigation
        previous = ui.Button(
            description="Previous",
            layout=ui.Layout(align_self="flex-end", justify_self="flex-end", margin="0px 8px"),  # NOSONAR
        )
        previous.on_click(self.ctrl.onclick_previous_from_upage_2)
        next_ = ui.Button(description="Next", layout=ui.Layout(align_self="flex-end", justify_self="flex-end"))
        next_.on_click(self.ctrl.onclick_next_from_upage_2)
        # Create the input format specifications section
        _label_layout = ui.Layout(width="205px")
        _wrapper_layout = ui.Layout(overflow_y="hidden")  # needed to prevent scrollbar from appearing on safari
        input_format_specifications_section = ui.VBox(  # vbox for the section
            children=[
                ui.GridBox(  # - gridbox for all format specification widgets except for "Scenarios to ignore"
                    children=(
                        ui.HBox(  # -- hbox for model name specs
                            children=(ui.Label(value="Model name *", layout=_label_layout), self.model_name_ddown),
                            layout=_wrapper_layout,
                        ),
                        ui.HBox(  # -- hbox for delimiter specs
                            children=(ui.Label(value="Delimiter *", layout=_label_layout), self.delimiter_ddown),
                            layout=_wrapper_layout,
                        ),
                        ui.HBox(  # -- hbox for header is included specs
                            children=(
                                ui.Label(value="Header is included *", layout=_label_layout),
                                self.header_is_included_chkbox,
                            ),
                            layout=_wrapper_layout,
                        ),
                        ui.HBox(  # -- hbox for number of initial lines to skip specs
                            children=(
                                ui.Label(value="Number of initial lines to skip *", layout=_label_layout),
                                self.lines_to_skip_txt,
                            ),
                            layout=_wrapper_layout,
                        ),
                    ),
                    layout=ui.Layout(width="100%", grid_template_columns="auto auto", grid_gap="4px 56px"),
                ),
                ui.HBox(  # - hbox for scenarios to ignore specs
                    children=(
                        ui.Label(value="Scenarios to ignore", layout=_label_layout),
                        self.scenarios_to_ignore_txt,
                    ),
                    layout=ui.Layout(margin="4px 0px 0px 0px"),
                ),
            ],
            layout=ui.Layout(padding="8px 0px 16px 0px"),
        )
        # Create the page
        return ui.VBox(  # vbox for page
            children=(
                ui.VBox(  # - vbox for the page's main components
                    children=(
                        ui.HTML(value="<b>Specify the format of the input data</b>"),  # -- input format specs title
                        input_format_specifications_section,  # -- input format specification section
                        ui.HTML(  # -- column assignment section title
                            value="<b>Assign columns from the input data to the output data</b>"
                        ),
                        CSS.assign_class(
                            ui.GridBox(  # -- gridbox representing the column assignment table
                                children=(
                                    ui.Box(children=(ui.Label(value="Model"),)),
                                    ui.Box(children=(ui.Label(value="Scenario"),)),
                                    ui.Box(children=(ui.Label(value="Region"),)),
                                    ui.Box(children=(ui.Label(value="Variable"),)),
                                    ui.Box(children=(ui.Label(value="Item"),)),
                                    ui.Box(children=(ui.Label(value="Unit"),)),
                                    ui.Box(children=(ui.Label(value="Year"),)),
                                    ui.Box(children=(ui.Label(value="Value"),)),
                                    ui.Box(children=(self.model_name_lbl,)),
                                    self.scenario_column_ddown,
                                    self.region_column_ddown,
                                    self.variable_column_ddown,
                                    self.item_column_ddown,
                                    self.unit_column_ddown,
                                    self.year_column_ddown,
                                    self.value_column_ddown,
                                )
                            ),
                            CSS.COLUMN_ASSIGNMENT_TABLE,
                        ),
                        ui.HTML(value="<b>Preview of the input data</b>"),  # -- input data preview title
                        self.input_data_preview_tbl,  # -- input data preview table
                        ui.HTML(value="<b>Preview of the output data</b>"),  # -- output data preview title
                        self.output_data_preview_tbl,  # -- output data preview table
                    ),
                    layout=ui.Layout(flex="1", width="900px", justify_content="center", align_items="flex-start"),
                ),
                ui.HBox(  # - hbox for the navigation buttons
                    children=[previous, next_], layout=ui.Layout(justify_content="flex-end", width="100%")
                ),
            ),
            layout=ui.Layout(flex="1", width="100%", align_items="center", justify_content="center"),
        )

    def _build_integrity_checking_page(self) -> ui.Box:
        """Build the integrity checking page"""
        # Create the control widgets
        # - create row download buttons
        # - we assume that the download paths are constant. else, the href values need to be updated during page update
        download_rows_field_issues_btn = ui.HTML(
            value=f"""
                <a
                    href="{str(self.model.STRUCTISSUEFILE_PATH)}" 
                    download="{str(self.model.STRUCTISSUEFILE_PATH.name)}"
                    class="{CSS.ICON_BUTTON}"
                    style="line-height:36px;"
                    title=""
                >
                    <i class="fa fa-download" style="margin-left: 4px;"></i>
                </a>
            """
        )
        download_rows_w_ignored_scenario_btn = ui.HTML(
            value=f"""
                <a
                    href="{str(self.model.IGNOREDSCENARIOFILE_PATH)}" 
                    download="{str(self.model.IGNOREDSCENARIOFILE_PATH.name)}"
                    class="{CSS.ICON_BUTTON}"
                    style="line-height:36px;"
                    title=""
                >
                    <i class="fa fa-download" style="margin-left: 4px;"></i>
                </a>
            """
        )
        download_duplicate_rows_btn = ui.HTML(
            value=f"""
                <a
                    href="{str(self.model.DUPLICATESFILE_PATH)}" 
                    download="{str(self.model.DUPLICATESFILE_PATH.name)}"
                    class="{CSS.ICON_BUTTON}"
                    style="line-height:36px;"
                    title=""
                >
                    <i class="fa fa-download" style="margin-left: 4px;"></i>
                </a>
            """
        )
        download_accepted_rows = ui.HTML(
            value=f"""
                <a
                    href="{str(self.model.ACCEPTEDFILE_PATH)}" 
                    download="{str(self.model.ACCEPTEDFILE_PATH.name)}"
                    class="{CSS.ICON_BUTTON}"
                    style="line-height:36px;"
                    title=""
                >
                    <i class="fa fa-download" style="margin-left: 4px;"></i>
                </a>
            """
        )
        # - create row summary labels
        self.rows_w_struct_issues_lbl = ui.Label(value="0")
        self.rows_w_ignored_scenario_lbl = ui.Label(value="0")
        self.duplicate_rows_lbl = ui.Label(value="0")
        self.accepted_rows_lbl = ui.Label(value="0")
        # - create bad labels table
        self.bad_labels_tbl = ui.HTML(
            value=f"""
            <table>
                <thead>
                    <th>Label</th>
                    <th>Associated column</th>
                    <th>Fix</th>
                </thead>
                <tbody>
                    {''' 
                    <tr>
                        <td>-</td>
                        <td>-</td>
                        <td>-</td>
                    <tr>
                    ''' * 3 
                    }
                </tbody>
            </table>
            """
        )
        self.bad_labels_tbl.add_class(CSS.BAD_LABELS_TABLE)
        # - create unknown labels table
        # - this is an interactive table, so the build process is a little different. essentially, we are creating a
        # - gridbox with a grey background and populating it with a bunch of boxes with a white background, making the
        # - gridbox look like a table. @date Aug 3, 2021
        # -- create the table's header row
        self._unknown_labels_tbl_cell_pool = [
            ui.Box(children=[ui.HTML(value="Label")]),
            ui.Box(children=[ui.HTML(value="Associated column")]),
            ui.Box(children=[ui.HTML(value="Closest Match")]),
            ui.Box(children=[ui.HTML(value="Fix")]),
            ui.Box(children=[ui.HTML(value="Override")]),
        ]
        # -- create the table's content, row by row
        # -- each row is in the format of [label, label, label, dropdown, checkbox]. to prevent us from having to
        # -- recreate each cell widget every time there is a page update (which is slow and might cause memory leak
        # -- in the browser) we create a pool of cell widgets and assign them as the gridbox's children.
        # -- TODO: Create a pool of rows instead of a pool of cells, which is more convenient to manage
        # -- @date Aug 3, 2021
        initial_nrows_in_pool = 10
        ncolumns = 5
        for row_index in range(initial_nrows_in_pool):
            dropdown = ui.Dropdown()
            # create a lambda that returns an onchange callback that can be assigned to an ipywidgets' dropdown
            # we only have one onchange callback in Controller for all the dropdowns in this table and it
            # requires the dropdown's row index as an argument. so, the onchange callback that our lambda returns will
            # call the Controller's onchange callback and pass the appropriate row index. @date Aug 3, 2021
            _get_dropdown_callback = lambda row_index_arg: lambda change: self.ctrl.onchange_fix_dropdown(
                change, row_index_arg
            )
            # create a lambda that returns an onchange callback that can be assigned to an ipywidgets' checkbox
            # the reasoning for this lambda is the same as above. @date Aug 3, 2021
            _get_checkbox_callback = lambda row_index_arg: lambda change: self.ctrl.onchange_override_checkbox(
                change, row_index_arg
            )
            dropdown.observe(_get_dropdown_callback(row_index), "value")
            checkbox = ui.Checkbox(indent=False, value=False, description="")
            checkbox.observe(_get_checkbox_callback(row_index), "value")
            self._unknown_labels_tbl_cell_pool += [
                ui.Box(children=[ui.HTML(value="-")]),
                ui.Box(children=[ui.HTML(value="-")]),
                ui.Box(children=[ui.HTML(value="-")]),
                ui.Box(children=[dropdown]),
                ui.Box(children=[checkbox]),
            ]
        initial_nrows_in_table = 4
        self.unknown_labels_tbl = ui.GridBox(
            children=self._unknown_labels_tbl_cell_pool[: initial_nrows_in_table * ncolumns]
        )
        self.unknown_labels_tbl.add_class(CSS.UNKNOWN_LABELS_TABLE)
        # - create page navigation buttons
        next_ = ui.Button(description="Next", layout=ui.Layout(align_self="flex-end", justify_self="flex-end"))
        next_.on_click(self.ctrl.onclick_next_from_upage_3)
        previous = ui.Button(
            description="Previous", layout=ui.Layout(align_self="flex-end", justify_self="flex-end", margin="0px 8px")
        )
        previous.on_click(self.ctrl.onclick_previous_from_upage_3)
        # Create the page
        return ui.VBox(  # vbox for page
            children=(
                ui.VBox(  # - vbox for the page's main components
                    children=(
                        ui.HTML(  # -- rows overview title
                            value='<b style="line-height:13px; margin-bottom:4px;">Rows overview</b>'
                        ),
                        ui.HTML(  # -- rows overview description
                            value=(
                                '<span style="line-height: 13px; color: var(--grey);">The'
                                " table shows an overview of the uploaded data's rows. The"
                                " rows can be downloaded to be analyzed.</span>"
                            )
                        ),
                        ui.HBox(  # -- hbox for rows overview table and row download buttons
                            children=[
                                CSS.assign_class(
                                    ui.GridBox(  # --- gridbox representing rows overview table
                                        # TODO: representing this table using ipywidgets HTML might be better
                                        # since the table is not interactive
                                        children=(
                                            ui.Box(
                                                children=(
                                                    ui.Label(
                                                        value=(
                                                            "Number of rows with structural issues (missing"
                                                            " fields, etc)"
                                                        )
                                                    ),
                                                )
                                            ),
                                            ui.Box(children=(self.rows_w_struct_issues_lbl,)),
                                            ui.Box(
                                                children=(
                                                    ui.Label(value="Number of rows containing an ignored scenario"),
                                                )
                                            ),
                                            ui.Box(children=(self.rows_w_ignored_scenario_lbl,)),
                                            ui.HTML(value="Number of duplicate rows"),
                                            ui.Box(children=(self.duplicate_rows_lbl,)),
                                            ui.Box(children=(ui.Label(value="Number of accepted rows"),)),
                                            ui.Box(children=(self.accepted_rows_lbl,)),
                                        ),
                                    ),
                                    CSS.ROWS_OVERVIEW_TABLE,
                                ),
                                ui.VBox(  # --- vbox for row download buttons
                                    children=[
                                        download_rows_field_issues_btn,
                                        download_rows_w_ignored_scenario_btn,
                                        download_duplicate_rows_btn,
                                        download_accepted_rows,
                                    ],
                                    layout=ui.Layout(margin="16px 0px 20px 0px"),
                                ),
                            ]
                        ),
                        ui.HTML(  # --- bad labels overview title
                            value='<b style="line-height:13px; margin-bottom:4px;">Bad labels overview</b>'
                        ),
                        ui.HTML(  # --- bad labels overview description
                            value=(
                                '<span style="line-height: 13px; color: var(--grey);">The table lists'
                                " labels that are recognized by the program but do not adhere to the correct"
                                " standard. They will be fixed automatically."
                            )
                        ),
                        self.bad_labels_tbl,  # --- bad labels overview table
                        ui.HTML(  # --- unknown labels overview title
                            value='<b style="line-height:13px; margin: 20px 0px 4px;">Unknown labels overview</b>'
                        ),
                        ui.HTML(  # --- unknown labels overview description
                            value=(
                                '<span style="line-height: 13px; color: var(--grey);">The table lists labels'
                                " that are not recognized by the program. Please fix or override the labels,"
                                " otherwise records containing them will be dropped."
                            )
                        ),
                        self.unknown_labels_tbl,  # --- unknown labels overview table
                    ),
                    layout=ui.Layout(
                        flex="1", width="850px", justify_content="center", align_items="flex-start", align_self="center"
                    ),
                ),
                ui.HBox(  # - hbox for navigation buttons
                    children=[previous, next_], layout=ui.Layout(justify_content="flex-end", width="100%")
                ),
            ),
            layout=ui.Layout(flex="1", width="100%", align_items="center", justify_content="center"),
        )

    def _build_plausibility_checking_page(self) -> ui.Box:
        # Create control widgets
        # - create control widgets for visualization tab bar
        value_tab_btn = ui.Button()
        value_tab_btn.on_click(self.ctrl.onclick_value_trends_tab)
        growth_tab_btn = ui.Button()
        growth_tab_btn.on_click(self.ctrl.onclick_growth_trends_tab)
        self.valuetrends_tabelement = ui.Box(children=[ui.Label(value="Value trends"), value_tab_btn])
        self.valuetrends_tabelement.add_class(CSS.VISUALIZATION_TAB__ELEMENT)
        self.valuetrends_tabelement.add_class(CSS.VISUALIZATION_TAB__ELEMENT__ACTIVE)
        self.growthtrends_tabelement = ui.Box(children=[ui.Label(value="Growth trends"), growth_tab_btn])
        self.growthtrends_tabelement.add_class(CSS.VISUALIZATION_TAB__ELEMENT)
        visualization_tabbar = ui.GridBox(
            children=[
                self.valuetrends_tabelement,
                self.growthtrends_tabelement,
            ]
        )
        visualization_tabbar.add_class(CSS.VISUALIZATION_TAB)
        # - create shared layouts for dropdowns & output areas
        _ddown_layout = ui.Layout(width="200px")
        _viz_output_layout = ui.Layout(
            margin="24px 0px 0px",
            justify_content="center",
            align_items="center",
            height="360px",
            width="100%",
            overflow="auto",
        )
        # - create control widgets for value trends tab content
        self.valuetrends_scenario_ddown = ui.Dropdown(layout=_ddown_layout, options=self.model.uploaded_scenarios)
        self.valuetrends_scenario_ddown.observe(self.ctrl.onchange_valuetrends_scenario, "value")
        self.valuetrends_region_ddown = ui.Dropdown(layout=_ddown_layout, options=self.model.uploaded_regions)
        self.valuetrends_region_ddown.observe(self.ctrl.onchange_valuetrends_region, "value")
        self.valuetrends_variable_ddown = ui.Dropdown(layout=_ddown_layout, options=self.model.uploaded_variables)
        self.valuetrends_variable_ddown.observe(self.ctrl.onchange_valuetrends_variable, "value")
        visualize_value_btn = ui.Button(description="Visualize", layout=ui.Layout(margin="24px 0px 0px 0px"))  # NOSONAR
        visualize_value_btn.on_click(self.ctrl.onclick_visualize_value_trends)
        self.valuetrends_viz_output = ui.Output(layout=_viz_output_layout)
        self.valuetrends_tabcontent = ui.VBox(
            children=[
                ui.GridBox(
                    children=(
                        ui.HTML(value="1. Scenario"),
                        self.valuetrends_scenario_ddown,
                        ui.HTML(value="2. Region"),
                        self.valuetrends_region_ddown,
                        ui.HTML(value="3. Variable"),
                        self.valuetrends_variable_ddown,
                    ),
                    layout=ui.Layout(
                        grid_template_columns="1fr 2fr 1fr 2fr 1fr 2fr", grid_gap="16px 16px", overflow_y="hidden"
                    ),
                ),
                visualize_value_btn,
                self.valuetrends_viz_output,
            ],
            layout=ui.Layout(align_items="center", padding="24px 0px 0px 0px", overflow_y="hidden"),
        )
        # - create control widgets for growth trends tab content
        self.growthtrends_scenario_ddown = ui.Dropdown(layout=_ddown_layout, options=self.model.uploaded_scenarios)
        self.growthtrends_scenario_ddown.observe(self.ctrl.onchange_growthtrends_scenario, "value")
        self.growthtrends_region_ddown = ui.Dropdown(layout=_ddown_layout, options=self.model.uploaded_regions)
        self.growthtrends_region_ddown.observe(self.ctrl.onchange_growthtrends_region, "value")
        self.growthtrends_variable_ddown = ui.Dropdown(layout=_ddown_layout, options=self.model.uploaded_variables)
        self.growthtrends_variable_ddown.observe(self.ctrl.onchange_growthtrends_variable, "value")
        visualize_growth_btn = ui.Button(description="Visualize", layout=ui.Layout(margin="24px 0px 0px 0px"))
        visualize_growth_btn.on_click(self.ctrl.onclick_visualize_growth_trends)
        self.growthtrends_viz_output = ui.Output(layout=_viz_output_layout)
        self.growthtrends_tabcontent = ui.VBox(
            children=[
                ui.GridBox(
                    children=(
                        ui.HTML(value="1. Scenario"),
                        self.growthtrends_scenario_ddown,
                        ui.HTML(value="2. Region"),
                        self.growthtrends_region_ddown,
                        ui.HTML(value="3. Variable"),
                        self.growthtrends_variable_ddown,
                    ),
                    layout=ui.Layout(
                        grid_template_columns="1fr 2fr 1fr 2fr 1fr 2fr", grid_gap="16px 16px", overflow_y="hidden"
                    ),
                ),
                visualize_growth_btn,
                self.growthtrends_viz_output,
            ],
            layout=ui.Layout(align_items="center", padding="24px 0px 0px 0px", overflow_y="hidden"),
        )
        self.growthtrends_tabcontent.add_class(CSS.DISPLAY_MOD__NONE)
        # - create control widgets for page navigation, submission, and download
        restart_submission = ui.Button(
            icon="refresh", layout=ui.Layout(align_self="center", padding="0px 0px"), tooltip="Restart submission"
        )
        restart_submission._dom_classes = (CSS.ICON_BUTTON, CSS.ICON_BUTTON_MOD__RESTART_SUBMISSION)
        restart_submission.on_click(self.ctrl.onclick_restart_submission)
        previous = ui.Button(
            description="Previous", layout=ui.Layout(align_self="flex-end", justify_self="flex-end", margin="0px 8px")
        )
        previous.on_click(self.ctrl.onclick_previous_from_upage_4)
        submit = ui.Button(
            description="Submit",
            button_style="success",
            layout=ui.Layout(align_self="flex-end", justify_self="flex-end"),
        )
        submit.on_click(self.ctrl.onclick_submit)
        # download = ui.HTML(
        #     f"""
        #         <a
        #             href="{str(self.model.outputfile_path)}"
        #             download="{str(self.model.outputfile_path.name)}"
        #             class="btn p-Widget jupyter-widgets jupyter-button widget-button mod-info"
        #             style="line-height:36px;"
        #             title=""
        #         >
        #             Download
        #             <i class="fa fa-download" style="margin-left: 4px;"></i>
        #         </a>
        #     """
        # )
        # Create page
        return ui.VBox(  # vbox for page
            children=(
                ui.VBox(  # - vbox for the page's main components
                    children=(
                        ui.HBox(  # -- hbox for [page title & instruction] and visualization tab bar
                            children=[
                                ui.VBox(  # --- vbox for the page title & instruction
                                    children=[
                                        ui.HTML(  # ---- page title
                                            value=(
                                                '<b style="line-height:13px; margin-bottom:4px;">Plausibility'
                                                " checking</b>"
                                            )
                                        ),
                                        ui.HTML(  # ---- page instruction
                                            value=(
                                                '<span style="line-height: 13px; color: var(--grey);">Visualize'
                                                " the uploaded data and verify that it looks plausible"
                                                " (Work-in-progress).</span>"
                                            )
                                        ),
                                    ],
                                    layout=ui.Layout(height="32px"),
                                ),
                                visualization_tabbar,  # --- visualization tab bar
                            ],
                            layout=ui.Layout(align_items="center", justify_content="space-between", width="100%"),
                        ),
                        self.valuetrends_tabcontent,  # -- value trends tab content
                        self.growthtrends_tabcontent,  # -- growth trends tab content
                    ),
                    layout=ui.Layout(width="900px", align_items="center", flex="1", justify_content="center"),
                ),
                ui.HBox(  # - hbox for navigation buttons
                    children=[restart_submission, previous, submit],
                    layout=ui.Layout(justify_content="flex-end", width="100%"),
                ),
            ),
            layout=ui.Layout(flex="1", width="100%", align_items="center", justify_content="center"),
        )

    def _build_admin_page(self) -> ui.Box:
        """Return an admin page"""
        table_rows = ""
        for row in self.model.get_submitted_files_info():
            table_rows += "<tr>"
            for colidx in range(len(row)):
                field = row[colidx]
                table_rows += f"<td>{field}</td>"
            table_rows += "</tr>"
        self.submissions_tbl = ui.HTML(
            value=f"""
            <table class="table">
                <thead>
                    <th style="width: 350px;">File</th>
                    <th style="width: 200px;">Associated Project</th>
                    <th style="width: 150px;">Status</th>
                </thead>
                <tbody>
                    {table_rows}
                    {''' 
                    <tr>
                        <td>-</td>
                        <td>-</td>
                        <td>-</td>
                    <tr>
                    ''' * (15 - len(table_rows))
                    }
                </tbody>
            </table>
        """
        )
        return ui.VBox(  # vbox for page
            children=[
                ui.VBox(
                    children=[
                        ui.HTML(value='<h4 style="margin: 16px 0px;">Submission history</h4>'),  # - table title
                        self.submissions_tbl,
                    ],
                    layout=ui.Layout(align_items="flex-start"),
                )
            ],
            layout=ui.Layout(
                flex="1",
                width="100%",
                align_items="center",
                justify_content="center",
            ),
        )
