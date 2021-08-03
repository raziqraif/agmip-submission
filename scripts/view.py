from __future__ import annotations  # Delay the evaluation of undefined types
from matplotlib import pyplot as plt
from threading import Timer
from typing import Callable, Optional, Union, List, Tuple, Any

import ipywidgets as ui
import numpy as np
from IPython.core.display import Javascript, clear_output, display
from IPython.core.display import HTML
from pandas.core.frame import DataFrame

from .namespaces import VisualizationTab

# The following is to silence complaints about assigning None to a non-optional type in constructor


class Icon:
    """Namespace for icon html objects"""

    WARNING = ui.HTML(
        value="""
        <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" fill="currentColor" class="bi bi-exclamation-triangle" viewBox="0 0 18 18"
            style="color: black; margin-right: 4px;" 
        >
            <path d="M7.938 2.016A.13.13 0 0 1 8.002 2a.13.13 0 0 1 .063.016.146.146 0 0 1 .054.057l6.857 11.667c.036.06.035.124.002.183a.163.163 0 0 1-.054.06.116.116 0 0 1-.066.017H1.146a.115.115 0 0 1-.066-.017.163.163 0 0 1-.054-.06.176.176 0 0 1 .002-.183L7.884 2.073a.147.147 0 0 1 .054-.057zm1.044-.45a1.13 1.13 0 0 0-1.96 0L.165 13.233c-.457.778.091 1.767.98 1.767h13.713c.889 0 1.438-.99.98-1.767L8.982 1.566z"/>
            <path d="M7.002 12a1 1 0 1 1 2 0 1 1 0 0 1-2 0zM7.1 5.995a.905.905 0 1 1 1.8 0l-.35 3.507a.552.552 0 0 1-1.1 0L7.1 5.995z"/>
        </svg>
        """
    )
    ERROR = ui.HTML(
        value="""
        <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" fill="currentColor" class="bi bi-exclamation-triangle" viewBox="0 0 18 18"
            style="color: white; margin-right: 4px;" 
        >
            <path d="M7.938 2.016A.13.13 0 0 1 8.002 2a.13.13 0 0 1 .063.016.146.146 0 0 1 .054.057l6.857 11.667c.036.06.035.124.002.183a.163.163 0 0 1-.054.06.116.116 0 0 1-.066.017H1.146a.115.115 0 0 1-.066-.017.163.163 0 0 1-.054-.06.176.176 0 0 1 .002-.183L7.884 2.073a.147.147 0 0 1 .054-.057zm1.044-.45a1.13 1.13 0 0 0-1.96 0L.165 13.233c-.457.778.091 1.767.98 1.767h13.713c.889 0 1.438-.99.98-1.767L8.982 1.566z"/>
            <path d="M7.002 12a1 1 0 1 1 2 0 1 1 0 0 1-2 0zM7.1 5.995a.905.905 0 1 1 1.8 0l-.35 3.507a.552.552 0 0 1-1.1 0L7.1 5.995z"/>
        </svg>
        """
    )
    INFO = ERROR
    SUCCESS = ui.HTML(
        value="""
        <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" fill="currentColor" class="bi bi-check-circle" viewBox="0 0 18 18"
            style="color: white; margin-right: 4px;" 
        >
            <path d="M8 15A7 7 0 1 1 8 1a7 7 0 0 1 0 14zm0 1A8 8 0 1 0 8 0a8 8 0 0 0 0 16z"/>
            <path d="M10.97 4.97a.235.235 0 0 0-.02.022L7.477 9.417 5.384 7.323a.75.75 0 0 0-1.06 1.06L6.97 11.03a.75.75 0 0 0 1.079-.02l3.992-4.99a.75.75 0 0 0-1.071-1.05z"/>
        </svg>
        """
    )


class Notification:
    """Namespace for notification variants"""

    ERROR = "error"
    INFO = "info"
    SUCCESS = "success"
    WARNING = "warning"
    _VARIANTS = [ERROR, INFO, SUCCESS, WARNING]

    FILE_UPLOAD_SUCCESS = "File uploaded successfully"
    INVALID_FILE_FORMAT = "File format must be CSV"
    PLEASE_UPLOAD = "Please upload a CSV file first"
    FIELDS_WERE_PREPOPULATED = "Some fields have been prepopulated for you"


class Delimiter:
    """
    Namespace for supported CSV delimiters and relevant utilities
    """

    # TODO: ipywidgets dropdown support having dual representation for selection values (ie, for frontend and backend),
    # so this class is not needed @ date Jul 27 2021
    _model_postfix = "_MODEL"
    _view_postfix = "_VIEW"
    COMMA_MODEL = ","
    COMMA_VIEW = "Comma  ( , )"
    SPACE_MODEL = " "
    SPACE_VIEW = "Space  (   )"
    SEMICOLON_MODEL = ";"
    SEMICOLON_VIEW = "Semicolon  ( ; )"
    TAB_MODEL = "\t"
    TAB_VIEW = "Tab  (      )"
    PIPE_MODEL = "|"
    PIPE_VIEW = "Pipe  ( | )"

    @classmethod
    def get_view(cls, delimiter_model: str) -> str:
        """Given a delimiter model, return a delimiter view"""
        if delimiter_model == "":  # Edge case
            return ""
        delimiter_model_names = [name for name in cls.__dict__.keys() if cls._model_postfix in name]
        delimiter_models = [getattr(cls, name) for name in delimiter_model_names]
        assert delimiter_model in delimiter_models
        for i in range(len(delimiter_models)):
            if delimiter_model == delimiter_models[i]:
                delimiter_model_name = delimiter_model_names[i]
                delimiter_view_name = delimiter_model_name.replace(cls._model_postfix, cls._view_postfix)
                return getattr(cls, delimiter_view_name)
        raise Exception("Cannot get delimiter view")

    @classmethod
    def get_model(cls, delimiter_view: str) -> str:
        """Given a delimiter view, return a delimiter model"""
        if delimiter_view == "":  # Edge case
            return ""
        delimiter_view_names = [name for name in cls.__dict__.keys() if cls._view_postfix in name]
        delimiter_views = [getattr(cls, name) for name in delimiter_view_names]
        assert delimiter_view in delimiter_views
        for i in range(len(delimiter_views)):
            if delimiter_view == delimiter_views[i]:
                delimiter_view_name = delimiter_view_names[i]
                delimiter_model_name = delimiter_view_name.replace(cls._view_postfix, cls._model_postfix)
                return getattr(cls, delimiter_model_name)
        raise Exception("Cannot get delimiter model")

    @classmethod
    def get_views(cls) -> list[str]:
        """Return all delimiter views"""
        delimiter_view_names = [name for name in cls.__dict__.keys() if cls._view_postfix in name]
        return [getattr(cls, name) for name in delimiter_view_names]

    @classmethod
    def get_models(cls) -> list[str]:
        """Return all delimiter models"""
        delimiter_model_names = [name for name in cls.__dict__.keys() if cls._model_postfix in name]
        return [getattr(cls, name) for name in delimiter_model_names]


class CSS:
    """Namespace for CSS classes declared in style.html and used inside Python"""

    APP = "rc-app-container"
    BAD_LABELS_TABLE = "rc-bad-labels-table"
    COLOR_MOD__BLACK = "rc-color-mod--black"
    COLOR_MOD__BLUE = "rc-color-mod--blue"
    COLOR_MOD__GREY = "rc-color-mod--grey"
    COLOR_MOD__WHITE = "rc-color-mod--white"
    COLUMN_ASSIGNMENT_TABLE = "rc-column-assignment-table"
    CURSOR_MOD__PROGRESS = "rc-cursor-mod--progress"
    CURSOR_MOD__WAIT = "rc-cursor-mod--wait"
    DISPLAY_MOD__NONE = "rc-display-mod--none"
    FILENAME_SNACKBAR = "rc-filename-snackbar"
    HEADER_BAR = "rc-header-bar"
    ICON_BUTTON = "rc-icon-button"
    NOTIFICATION = "rc-notification"
    NOTIFICATION__ERROR = "rc-notification--error"
    NOTIFICATION__INFO = "rc-notification--info"
    NOTIFICATION__SHOW = "rc-notification--show"
    NOTIFICATION__SUCCESS = "rc-notification--success"
    NOTIFICATION__WARNING = "rc-notification--warning"
    PREVIEW_TABLE = "rc-preview-table"
    ROWS_OVERVIEW_TABLE = "rc-rows-overview-table"
    STEPPER_EL = "rc-stepper-element"
    STEPPER_EL__ACTIVE = "rc-stepper-element--active"
    STEPPER_EL__CURRENT = "rc-stepper-element--current"
    STEPPER_EL__INACTIVE = "rc-stepper-element--inactive"
    STEPPER_EL__NUMBER = "rc-stepper-element__number"
    STEPPER_EL__SEPARATOR = "rc-stepper-element__separator"
    STEPPER_EL__TITLE = "rc-stepper-element__title"
    UA = "rc-upload-area"
    UA__BACKGROUND = "rc-upload-area__background"
    UA__FILE_UPLOADER = "rc-upload-area__file-uploader"
    UA__OVERLAY = "rc-upload-area__overlay"
    UA__FILE_LABEL = "rc-upload-area__file-label"
    UNKNOWN_LABELS_TABLE = "rc-unknown-labels-table"
    VISUALIZATION_TAB = "rc-visualization-tab"
    VISUALIZATION_TAB__ELEMENT = "rc-visualization-tab__element"
    VISUALIZATION_TAB__ELEMENT__ACTIVE = "rc-visualization-tab__element--active"

    @classmethod
    def assign_class(cls, widget: ui.DOMWidget, class_name: str) -> ui.DOMWidget:
        """Assign a CSS class to a widget and returns the widget back"""
        # Get attribute names by filtering out method names from __dict__.keys()
        attribute_names = [name for name in cls.__dict__.keys() if name[:1] != "__"]
        defined_css_classes = [getattr(cls, name) for name in attribute_names]
        assert class_name in defined_css_classes
        assert isinstance(widget, ui.DOMWidget)
        widget.add_class(class_name)
        return widget

    @classmethod
    def get_cursor_mod_classes(cls) -> list[str]:
        name_prefix = "CURSOR_MOD__"
        names = [name for name in cls.__dict__.keys() if name_prefix in name]
        return [getattr(cls, name) for name in names]


PLOT_HEIGHT = 11
PLOT_WIDTH = 5.5


def set_options(widget: ui.Dropdown, options: Tuple | List, onchange_callback) -> None:
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
    # TODO: replace this with a proper test suite
    def __init__(self):
        # Import MVC classes here to prevent circular import problem
        from .controller import Controller
        from .model import Model

        # MVC objects self.model: Model
        self.model: Model
        self.ctrl: Controller

        # Base app's widgets that need to be manipulated
        self.app_container = ui.Box()
        self.page_container = ui.Box()
        self.page_stepper = ui.Box()
        self.notification = ui.Box()
        self.notification_timer = Timer(0.0, lambda x: None)
        # Widgets in the file upload page that need to be manipulated
        self.ua_file_label = ui.Label()  # ua here stands for "upload area"
        self.uploaded_file_name_box = ui.Box()
        # Widgets in the data specification page that need to be manipulated
        # - parsing widgets
        self.model_name_ddown = ui.Dropdown()
        self.delimiter_ddown = ui.Dropdown()
        self.header_is_included_chkbox = ui.Checkbox()
        self.lines_to_skip_txt = ui.Text()
        self.scenarios_to_ignore_txt = ui.Textarea()
        # - column assignment widgets
        self.model_name_lbl = ui.Label()
        self.scenario_column_ddown = ui.Dropdown()
        self.region_column_ddown = ui.Dropdown()
        self.variable_column_ddown = ui.Dropdown()
        self.item_column_ddown = ui.Dropdown()
        self.unit_column_ddown = ui.Dropdown()
        self.year_column_ddown = ui.Dropdown()
        self.value_column_ddown = ui.Dropdown()
        # - preview tables
        self.input_data_preview_tbl = ui.GridBox()
        self.output_data_preview_tbl = ui.GridBox()
        self._input_data_table_childrenpool: list[ui.Box] = []
        # Widgets in the integrity checking page that need to be manipulated
        self.duplicate_rows_lbl = ui.Label()
        self.rows_w_struct_issues_lbl = ui.Label()
        self.rows_w_ignored_scenario_lbl = ui.Label()
        self.accepted_rows_lbl = ui.Label()
        self.bad_labels_tbl = ui.HTML()
        self.unknown_labels_tbl = ui.GridBox()
        self._unknown_labels_tbl_childrenpool: list[ui.Box] = []
        # Widgets in the plausibility checking page that need to be manipulated
        # - viz tab elements & tab contents
        self.valuetrends_tabelement = ui.Box()
        self.valuetrends_tabcontent = ui.Box()
        self.growthtrends_tabelement = ui.Box()
        self.growthtrends_tabcontent = ui.Box()
        self.boxplot_tabelement = ui.Box()
        self.boxplot_tabcontent = ui.Box()
        # - widgets for value trends viz
        self.valuetrends_scenario_ddown = ui.Dropdown()
        self.valuetrends_region_ddown = ui.Dropdown()
        self.valuetrends_variable_ddown = ui.Dropdown()
        self.valuetrends_viz_output = ui.Output()
        # - widgets for growth trends viz
        self.growthtrends_scenario_ddown = ui.Dropdown()
        self.growthtrends_region_ddown = ui.Dropdown()
        self.growthtrends_variable_ddown = ui.Dropdown()
        self.growthtrends_viz_output = ui.Output()
        # - widgets for box plot viz
        self.boxplot_scenario_ddown = ui.Dropdown()
        self.boxplot_region_ddown = ui.Dropdown()
        self.boxplot_variable_ddown = ui.Dropdown()
        self.boxplot_item_ddown = ui.Dropdown()
        self.boxplot_year_ddown = ui.Dropdown()
        self.boxplot_viz_output = ui.Output()

    def intro(self, model: Model, ctrl: Controller) -> None:  # type: ignore # noqa
        """Introduce MVC modules to each other"""
        self.model = model
        self.ctrl = ctrl

    def display(self) -> None:
        """Build and show notebook user interface"""
        from scripts.model import JSAppModel

        self.app_container = self._build_app()
        # Display the appropriate html files and our ipywidgets app
        display(HTML(filename="style.html"))
        display(self.app_container)
        # Embed Javascript app model in Javascript context
        javascript_model: JSAppModel = self.model.javascript_model
        display(HTML(f"<script> APP_MODEL = {javascript_model.serialize()}</script>"))
        display(HTML(filename="script.html"))

    def modify_cursor(self, new_cursor_mod_class: Optional[str]) -> None:
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
        self.notification_timer.cancel()
        # Reset the notification's DOM classes
        # This is important because we implement a clickaway listener in JS which removes a DOM class from the
        # notification view without notifying the notification model. Doing this will reset the DOM classes that both
        # the notification models in server-side & client-side are maintaining
        self.notification._dom_classes = (CSS.NOTIFICATION,)
        # Update notification content
        notification_text = self.notification.children[1]
        assert isinstance(notification_text, ui.Label)
        notification_text.value = content
        # Update notification visibility & style
        if variant == Notification.SUCCESS:
            self.notification.children = (Icon.SUCCESS, notification_text)
            self.notification._dom_classes = (CSS.NOTIFICATION, CSS.NOTIFICATION__SHOW, CSS.NOTIFICATION__SUCCESS)
            notification_text._dom_classes = (CSS.COLOR_MOD__WHITE,)
        elif variant == Notification.INFO:
            self.notification.children = (Icon.INFO, notification_text)
            self.notification._dom_classes = (CSS.NOTIFICATION, CSS.NOTIFICATION__SHOW, CSS.NOTIFICATION__INFO)
            notification_text._dom_classes = (CSS.COLOR_MOD__WHITE,)
        elif variant == Notification.WARNING:
            self.notification.children = (Icon.WARNING, notification_text)
            self.notification._dom_classes = (CSS.NOTIFICATION, CSS.NOTIFICATION__SHOW, CSS.NOTIFICATION__WARNING)
            notification_text._dom_classes = (CSS.COLOR_MOD__BLACK,)
        elif variant == Notification.ERROR:
            self.notification.children = (Icon.ERROR, notification_text)
            self.notification._dom_classes = (CSS.NOTIFICATION, CSS.NOTIFICATION__SHOW, CSS.NOTIFICATION__ERROR)
            notification_text._dom_classes = (CSS.COLOR_MOD__WHITE,)
        else:
            assert len("Variant does not exists") == 0
        # Create a timer to hide notification after X seconds
        self.notification_timer = Timer(3.5, self.notification.remove_class, args=[CSS.NOTIFICATION__SHOW])
        self.notification_timer.start()

    def show_modal_dialog(self, title: str, body: str) -> None:
        """Show modal dialog"""
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
        NUM_OF_PAGES = len(self.page_container.children)
        assert self.model.current_page > 0 and self.model.current_page <= NUM_OF_PAGES
        assert self.model.furthest_active_page > 0 and self.model.furthest_active_page <= NUM_OF_PAGES
        current_page_index = self.model.current_page - 1
        # Update visibility of pages and style of page stepper elements
        for page_index in range(0, NUM_OF_PAGES):
            page = self.page_container.children[page_index]
            stepper_el = self.page_stepper.children[page_index]
            assert isinstance(page, ui.Box)
            assert isinstance(stepper_el, ui.Box)
            if page_index == current_page_index:
                page.remove_class(CSS.DISPLAY_MOD__NONE)
                stepper_el._dom_classes = (CSS.STEPPER_EL, CSS.STEPPER_EL__CURRENT)
            else:
                page.add_class(CSS.DISPLAY_MOD__NONE)
                stepper_el._dom_classes = (
                    (CSS.STEPPER_EL, CSS.STEPPER_EL__ACTIVE)
                    if page_index < self.model.furthest_active_page
                    else (CSS.STEPPER_EL, CSS.STEPPER_EL__INACTIVE)
                )

    def update_file_upload_page(self) -> None:
        """Update the file upload page"""
        children_: Tuple[ui.HTML, ui.Box] = self.uploaded_file_name_box.children
        no_file_uploaded_widget = children_[0]
        file_uploaded_widget = children_[1]

        if self.model.uploadedfile_name != "":
            no_file_uploaded_widget.add_class(CSS.DISPLAY_MOD__NONE)
            file_uploaded_widget.remove_class(CSS.DISPLAY_MOD__NONE)
            children: tuple[ui.Label, ui.Button] = file_uploaded_widget.children
            label_widget = children[0]
            label_widget.value = self.model.uploadedfile_name
        else:
            file_uploaded_widget.add_class(CSS.DISPLAY_MOD__NONE)
            no_file_uploaded_widget.remove_class(CSS.DISPLAY_MOD__NONE)

        # Reset the hidden filename value
        self.ua_file_label.value = ""

    def update_data_specification_page(self):
        """Update the state of data specification page"""
        # TODO: Replace this with a proper test suite
        assert self.DATA_SPEC_PAGE_IS_BEING_UPDATED != True
        self.DATA_SPEC_PAGE_IS_BEING_UPDATED = True
        # Format specification controls
        set_options(self.model_name_ddown, ("", *self.model.model_names), self.ctrl.onchange_model_name_dropdown)
        self.model_name_ddown.value = self.model.model_name
        set_options(self.delimiter_ddown, ("", *Delimiter.get_views()), self.ctrl.onchange_delimiter_dropdown)
        self.delimiter_ddown.value = Delimiter.get_view(self.model.delimiter)
        self.header_is_included_chkbox.value = self.model.header_is_included
        self.lines_to_skip_txt.value = str(self.model.lines_to_skip)
        self.scenarios_to_ignore_txt.value = self.model.scenarios_to_ignore_str
        # Column assignment controls
        column_options = ("", *self.model.column_assignment_options)
        self.model_name_lbl.value = self.model.model_name if len(self.model.model_name) > 0 else "<Model Name>"
        set_options(self.scenario_column_ddown, column_options, self.ctrl.onchange_scenario_column_dropdown)
        self.scenario_column_ddown.value = self.model.assigned_scenario_column
        set_options(self.region_column_ddown, column_options, self.ctrl.onchange_region_column_dropdown)
        self.region_column_ddown.value = self.model.assigned_region_column
        set_options(self.variable_column_ddown, column_options, self.ctrl.onchange_variable_column_dropdown)
        self.variable_column_ddown.value = self.model.assigned_variable_column
        set_options(self.item_column_ddown, column_options, self.ctrl.onchange_item_column_dropdown)
        self.item_column_ddown.value = self.model.assigned_item_column
        set_options(self.unit_column_ddown, column_options, self.ctrl.onchange_unit_column_dropdown)
        self.unit_column_ddown.value = self.model.assigned_unit_column
        set_options(self.year_column_ddown, column_options, self.ctrl.onchange_year_column_dropdown)
        self.year_column_ddown.value = self.model.assigned_year_column
        set_options(self.value_column_ddown, column_options, self.ctrl.onchange_value_column_dropdown)
        self.value_column_ddown.value = self.model.assigned_value_column
        # Upload data preview table
        table_content = self.model.input_data_preview_content
        number_of_columns = table_content.shape[1]
        table_content = table_content.flatten()
        # -Increase pool size if it's insufficient
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
        # Output data preview table
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
        # TODO: remove this after a proper test suite has been created
        self.DATA_SPEC_PAGE_IS_BEING_UPDATED = False

    def update_integrity_checking_page(self) -> None:
        """Update the integrity checking page"""
        # Update row summaries
        self.rows_w_struct_issues_lbl.value = "{:,}".format(self.model.nrows_w_struct_issue)
        self.rows_w_ignored_scenario_lbl.value = "{:,}".format(self.model.nrows_w_ignored_scenario)
        self.duplicate_rows_lbl.value = "{:,}".format(self.model.nrows_duplicates)
        self.accepted_rows_lbl.value = "{:,}".format(self.model.nrows_accepted)
        # Update bad labels table
        _table_rows = ""
        for row in self.model.bad_labels_table:
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
        # Update unknown labels table
        # - make sure the children pool is large enough
        nrowsneeded = len(self.model.unknown_labels_table)
        nrowssupported = int((len(self._unknown_labels_tbl_childrenpool) - 5) / 5)  # -5 to account for header row
        if nrowsneeded > nrowssupported:
            for row_index in range(nrowssupported, nrowsneeded):
                dropdown = ui.Dropdown()
                # the following lambda return a callback that can be called by ipywidgets
                _get_dropdown_callback = lambda row_index: lambda change: self.ctrl.onchange_fix_dropdown(
                    change, row_index
                )
                dropdown.observe(_get_dropdown_callback(row_index), "value")
                checkbox = ui.Checkbox(indent=False, value=False, description="")
                # the following lambda return a callback that can be called by ipywidgets
                _get_checkbox_callback = lambda row_index: lambda change: self.ctrl.onchange_override_checkbox(
                    change, row_index
                )
                checkbox.observe(_get_checkbox_callback(row_index), "value")
                self._unknown_labels_tbl_childrenpool += [
                    ui.Box(children=[ui.Label(value="-")]),
                    ui.Box(children=[ui.Label(value="-")]),
                    ui.Box(children=[ui.Label(value="-")]),
                    ui.Box(children=[dropdown]),
                    ui.Box(children=[checkbox]),
                ]
        ui.Box()
        # - update the table entries
        for row_index in range(nrowsneeded):
            row = self.model.unknown_labels_table[row_index]
            poolstartindex = (row_index * 5) + 5  # +5 to account for header row
            unknownlabel_w, associatedcolumn_w, closestmatch_w, fix_w, override_w = [
                wrapper.children[0]
                for wrapper in self._unknown_labels_tbl_childrenpool[poolstartindex : poolstartindex + 5]
            ]
            assert isinstance(unknownlabel_w, ui.Label)
            assert isinstance(associatedcolumn_w, ui.Label)
            assert isinstance(closestmatch_w, ui.Label)
            assert isinstance(fix_w, ui.Dropdown)
            assert isinstance(override_w, ui.Checkbox)
            unknownlabel, associatedcolumn, closestmatch, fix, override = row
            unknownlabel_w.value = unknownlabel
            unknownlabel_w.description = unknownlabel
            unknownlabel_w.description_tooltip = unknownlabel
            associatedcolumn_w.value = associatedcolumn
            closestmatch_w.value = closestmatch
            fix_w.value = None
            if associatedcolumn == "-":
                fix_w.options = [""]
            elif associatedcolumn == "Scenario":
                fix_w.options = ["", *self.model.valid_scenarios]
            elif associatedcolumn == "Region":
                fix_w.options = ["", *self.model.valid_regions]
            elif associatedcolumn == "Variable":
                fix_w.options = ["", *self.model.valid_variables]
            elif associatedcolumn == "Item":
                fix_w.options = ["", *self.model.valid_items]
            elif associatedcolumn == "Unit":
                fix_w.options = ["", *self.model.valid_units]
            else:
                raise Exception("Unexpected associated column")
            fix_w.value = fix
            override_w.value = override
        self.unknown_labels_tbl.children = self._unknown_labels_tbl_childrenpool[: (nrowsneeded + 1) * 5]

    def update_plausibility_checking_page(self) -> None:
        """Update the plausibility checking page"""
        # Update tab elements and tab content
        is_active: Callable[[VisualizationTab], bool] = lambda tab: self.model.active_visualization_tab == tab
        if is_active(VisualizationTab.VALUE_TRENDS):
            self.valuetrends_tabelement.add_class(CSS.VISUALIZATION_TAB__ELEMENT__ACTIVE)
            self.valuetrends_tabcontent.remove_class(CSS.DISPLAY_MOD__NONE)
        else:
            self.valuetrends_tabelement.remove_class(CSS.VISUALIZATION_TAB__ELEMENT__ACTIVE)
            self.valuetrends_tabcontent.add_class(CSS.DISPLAY_MOD__NONE)
        if is_active(VisualizationTab.GROWTH_TRENDS):
            self.growthtrends_tabelement.add_class(CSS.VISUALIZATION_TAB__ELEMENT__ACTIVE)
            self.growthtrends_tabcontent.remove_class(CSS.DISPLAY_MOD__NONE)
        else:
            self.growthtrends_tabelement.remove_class(CSS.VISUALIZATION_TAB__ELEMENT__ACTIVE)
            self.growthtrends_tabcontent.add_class(CSS.DISPLAY_MOD__NONE)
        if is_active(VisualizationTab.BOX_PLOT):
            self.boxplot_tabelement.add_class(CSS.VISUALIZATION_TAB__ELEMENT__ACTIVE)
            self.boxplot_tabcontent.remove_class(CSS.DISPLAY_MOD__NONE)
        else:
            self.boxplot_tabelement.remove_class(CSS.VISUALIZATION_TAB__ELEMENT__ACTIVE)
            self.boxplot_tabcontent.add_class(CSS.DISPLAY_MOD__NONE)
        # Update the dropdown options and values in the value trends tab
        # - scenario dropdown
        set_options(
            self.valuetrends_scenario_ddown, self.model.uploaded_scenarios, self.ctrl.onchange_valuetrends_scenario
        )
        self.valuetrends_scenario_ddown.value = self.model.valuetrends_scenario
        # - region dropdown
        set_options(self.valuetrends_region_ddown, self.model.uploaded_regions, self.ctrl.onchange_valuetrends_region)
        self.valuetrends_region_ddown.value = self.model.valuetrends_region
        # - variable dropdown
        set_options(
            self.valuetrends_variable_ddown, self.model.uploaded_variables, self.ctrl.onchange_valuetrends_variable
        )
        self.valuetrends_variable_ddown.value = self.model.valuetrends_variable
        # Update the dropdown options and values in the growth trends tab
        # - scenario dropdown
        set_options(
            self.growthtrends_scenario_ddown, self.model.uploaded_scenarios, self.ctrl.onchange_growthtrends_scenario
        )
        self.growthtrends_scenario_ddown.value = self.model.growthtrends_scenario
        # - region dropdown
        set_options(self.growthtrends_region_ddown, self.model.uploaded_regions, self.ctrl.onchange_growthtrends_region)
        self.growthtrends_region_ddown.value = self.model.growthtrends_region
        # - variable dropdown
        set_options(
            self.growthtrends_variable_ddown, self.model.uploaded_variables, self.ctrl.onchange_growthtrends_variable
        )
        self.growthtrends_variable_ddown.value = self.model.growthtrends_variable
        # Update dropdown options for boxplot visualization
        self.boxplot_scenario_ddown.options = self.model.uploaded_scenarios
        self.boxplot_region_ddown.options = self.model.uploaded_regions
        self.boxplot_variable_ddown.options = self.model.uploaded_variables
        self.boxplot_item_ddown.options = self.model.uploaded_items
        self.boxplot_year_ddown.options = self.model.uploaded_years

    def visualize_value_trends(self) -> None:
        """Visualize value trends"""
        with self.valuetrends_viz_output:
            clear_output(wait=True)
            _, axes = plt.subplots(figsize=(PLOT_HEIGHT, PLOT_WIDTH))  # size in inches
            if self.model.valuetrends_vis_groupedtable is not None:
                # Make sure we have enough colors for all lines
                # https://stackoverflow.com/a/35971096/16133077
                num_plots = self.model.valuetrends_vis_groupedtable.ngroups
                axes.set_prop_cycle(plt.cycler("color", plt.cm.jet(np.linspace(0, 1, num_plots))))  # type: ignore
                # Multi-line chart
                # https://stackoverflow.com/questions/29233283/plotting-multiple-lines-in-different-colors-with-pandas-dataframe?answertab=votes#tab-top
                for key, group in self.model.valuetrends_vis_groupedtable:
                    axes = group.plot(
                        ax=axes,
                        kind="line",
                        x=self.model.valuetrends_year_colname,
                        y=self.model.valuetrends_value_colname,
                        label=key,
                    )
            axes.set_xlabel("Year")
            axes.set_ylabel("Value")
            plt.title("Value Trends")
            plt.grid()
            plt.show()

    def visualize_growth_trends(self) -> None:
        """Visualize growth trends"""
        with self.growthtrends_viz_output:
            clear_output(wait=True)
            _, axes = plt.subplots(figsize=(PLOT_HEIGHT, PLOT_WIDTH))  # size in inches
            if self.model.growthtrends_vis_groupedtable is not None:
                # Make sure we have enough colors for all lines
                # https://stackoverflow.com/a/35971096/16133077
                num_plots = self.model.growthtrends_vis_groupedtable.ngroups
                axes.set_prop_cycle(plt.cycler("color", plt.cm.jet(np.linspace(0, 1, num_plots))))  # type: ignore
                # Multi-line chart
                # https://stackoverflow.com/questions/29233283/plotting-multiple-lines-in-different-colors-with-pandas-dataframe?answertab=votes#tab-top
                for key, group in self.model.growthtrends_vis_groupedtable:
                    assert isinstance(group, DataFrame)
                    # group.sort_values([self.model.growthtrends_year_colname], inplace=True)
                    # growtrates_colname = "GrowthRates"
                    # group[growtrates_colname] = 0.0
                    # group[growtrates_colname].apply(lambda x: 100 * (pow(x/x.shift(1), 1/)))
                    axes = group.plot(
                        ax=axes,
                        kind="line",
                        x=self.model.growthtrends_year_colname,
                        y=self.model.growthtrends_growthvalue_colname,
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
        PAGE_TITLES = ["File Upload", "Data Specification", "Integrity Checking", "Plausibility Checking"]
        NUM_OF_PAGES = len(PAGE_TITLES)
        # Create notification widget
        notification_text = ui.Label(value="")
        self.notification = ui.HBox(children=(Icon.SUCCESS, notification_text))
        self.notification.add_class(CSS.NOTIFICATION)
        # Create stepper
        stepper_children = []
        for page_index in range(0, NUM_OF_PAGES):
            _number = ui.HTML(value=str(page_index + 1))
            _number.add_class(CSS.STEPPER_EL__NUMBER)
            _title = ui.Label(value=PAGE_TITLES[page_index])
            _title.add_class(CSS.STEPPER_EL__TITLE)
            _separator = ui.HTML(value="<hr width=48px/>")
            _separator.add_class(CSS.STEPPER_EL__SEPARATOR)
            stepper_element = (
                ui.Box(children=[_number, _title])
                if page_index == 0
                else ui.Box(children=[_separator, _number, _title])
            )
            stepper_element.add_class(CSS.STEPPER_EL)
            stepper_element.add_class(CSS.STEPPER_EL__CURRENT if page_index == 0 else CSS.STEPPER_EL__INACTIVE)
            stepper_children += [stepper_element]
        self.page_stepper = ui.HBox(children=stepper_children)
        # self.page_stepper.add_class(CSS.STEPPER)
        # Create app pages & page container
        self.page_container = ui.Box(
            children=[
                self._build_file_upload_page(),
                self._build_data_specification_page(),
                self._build_integrity_checking_page(),
                self._build_plausibility_checking_page(),
            ],
            layout=ui.Layout(flex="1", width="100%"),  # page container stores the current page
        )
        # Hide all pages, except for the first one
        for page in self.page_container.children[1:]:
            page.add_class(CSS.DISPLAY_MOD__NONE)
        app = ui.VBox(  # app container
            children=[
                self.notification,
                CSS.assign_class(ui.HTML(value=APP_TITLE), CSS.HEADER_BAR),  # -header bar
                ui.VBox(  # -body container
                    children=[self.page_stepper, self.page_container],  # --page stepper, page container
                    layout=ui.Layout(flex="1", align_items="center", padding="36px 48px"),
                ),
            ],
        )
        app.add_class(CSS.APP)
        return app

    def _build_file_upload_page(self) -> ui.Box:
        """Build the file upload page"""
        from scripts.model import JSAppModel

        # Create file upload area / ua
        ua_background = ui.HBox(
            children=[
                ui.HTML(value=f'<strong class="{CSS.COLOR_MOD__BLUE}"">&#128206;&nbsp;Add a CSV file&nbsp;</strong>'),
                ui.HTML(value=f'<div class="{CSS.COLOR_MOD__GREY}"">from your computer</div>'),
            ]
        )
        ua_background.add_class(CSS.UA__BACKGROUND)
        ua_overlay = ui.HTML(
            value=f"""
            <input class="{CSS.UA__FILE_UPLOADER}" type="file" title="Click to browse" accept=".csv">
            """
        )
        ua_overlay.add_class(CSS.UA__OVERLAY)
        self.ua_file_label = ui.Label(value="")
        self.ua_file_label.add_class(CSS.UA__FILE_LABEL)
        self.ua_file_label.observe(self.ctrl.onchange_ua_file_label, "value")
        upload_area = ui.Box(
            children=[ua_background, ua_overlay, self.ua_file_label],
            layout=ui.Layout(margin="20px 0px"),
        )
        upload_area._dom_classes = [CSS.UA]
        # Store the model id of file label in the js model (so that the label can be manipulated within js context)
        javascript_model: JSAppModel = self.model.javascript_model
        javascript_model.ua_file_label_model_id = self.ua_file_label.model_id
        # Create uploaded filename box
        # - create snackbar to tell the user that no file has been uploaded
        no_file_uploaded = ui.HTML(
            value=(
                '<div style="width: 500px; line-height: 36px; text-align: center; background: rgba(75, 85, 99, 0.1);'
                ' color: var(--grey);"> No file uploaded </div>'
            )
        )
        # -Create snackbar to show the uploaded file's name
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
        uploaded_file_snackbar.add_class(CSS.DISPLAY_MOD__NONE)  # By default this snackbar is hidden
        # - create the box
        self.uploaded_file_name_box = ui.Box(children=[no_file_uploaded, uploaded_file_snackbar])
        self.uploaded_file_name_box.layout = ui.Layout(margin="0px 0px 24px 0px")
        # Create project selection
        associatedprojects_select = ui.SelectMultiple(options=self.model.associated_projects_pool)
        associatedprojects_select.observe(self.ctrl.onchange_associated_projects, "value")
        associatedprojects_select.layout = ui.Layout(margin="20px 0px 0px 0px", width="500px")
        # Create navigation button
        next_button = ui.Button(description="Next", layout=ui.Layout(align_self="flex-end", justify_self="flex-end"))
        next_button.on_click(self.ctrl.onclick_next_from_page_1)
        # Create page
        return ui.VBox(  # page
            children=[
                ui.VBox(  # -container to fill up the space above navigation buttons
                    children=[
                        ui.HBox(
                            children=[
                                ui.HTML(value='<h4 style="margin: 0px;">1) Upload a data file</h4>'),
                                ui.HTML(
                                    value=f"""
                                    <a
                                        href="{str(self.model.samplefile_path)}" 
                                        download="{str(self.model.samplefile_path.name)}"
                                        class="{CSS.ICON_BUTTON}"
                                        style="line-height:16px; height:16px"
                                        title="Download a sample file"
                                    >
                                        <i class="fa fa-download"></i>
                                    </a>
                                    """
                                ),
                            ],
                            layout=ui.Layout(width="500px", align_items="flex-end"),
                        ),
                        upload_area,  # --upload area
                        self.uploaded_file_name_box,
                        ui.HTML(value='<h4 style="margin: 0px;">2) Select associated projects</h4>'),
                        associatedprojects_select,
                    ],
                    layout=ui.Layout(flex="1", justify_content="center"),
                ),
                ui.HBox(children=[next_button], layout=ui.Layout(align_self="flex-end")),  # -navigation button box
            ],
            layout=ui.Layout(flex="1", width="100%", align_items="center", justify_content="center"),
        )

    def _build_data_specification_page(self) -> ui.Box:
        """Build the data specification page"""
        # Create all control widgets in this page
        # -specification widgets
        control_layout = ui.Layout(flex="1 1", max_width="100%")
        self.model_name_ddown = ui.Dropdown(value="", options=[""], layout=control_layout)
        self.model_name_ddown.observe(self.ctrl.onchange_model_name_dropdown, "value")
        self.header_is_included_chkbox = ui.Checkbox(indent=False, value=False, description="", layout=control_layout)
        self.header_is_included_chkbox.observe(self.ctrl.onchange_header_is_included_checkbox, "value")
        self.lines_to_skip_txt = ui.Text(layout=control_layout, continuous_update=False)
        self.lines_to_skip_txt.observe(self.ctrl.onchange_lines_to_skip_text, "value")
        self.delimiter_ddown = ui.Dropdown(value="", options=[""], layout=control_layout)
        self.delimiter_ddown.observe(self.ctrl.onchange_delimiter_dropdown, "value")
        self.scenarios_to_ignore_txt = ui.Textarea(
            placeholder="(Optional) Enter comma-separated scenario values",
            layout=ui.Layout(flex="1", height="72px"),
            continuous_update=False,
        )
        self.scenarios_to_ignore_txt.observe(self.ctrl.onchange_scenarios_to_ignore_text, "value")
        # -column assignment widgets
        self.model_name_lbl = ui.Label(value="")
        self.scenario_column_ddown = ui.Dropdown(value="", options=[""], layout=control_layout)
        self.scenario_column_ddown.observe(self.ctrl.onchange_scenario_column_dropdown, "value")
        self.region_column_ddown = ui.Dropdown(value="", options=[""], layout=control_layout)
        self.region_column_ddown.observe(self.ctrl.onchange_region_column_dropdown, "value")
        self.variable_column_ddown = ui.Dropdown(value="", options=[""], layout=control_layout)
        self.variable_column_ddown.observe(self.ctrl.onchange_variable_column_dropdown, "value")
        self.item_column_ddown = ui.Dropdown(value="", options=[""], layout=control_layout)
        self.item_column_ddown.observe(self.ctrl.onchange_item_column_dropdown, "value")
        self.unit_column_ddown = ui.Dropdown(value="", options=[""], layout=control_layout)
        self.unit_column_ddown.observe(self.ctrl.onchange_unit_column_dropdown, "value")
        self.year_column_ddown = ui.Dropdown(value="", options=[""], layout=control_layout)
        self.year_column_ddown.observe(self.ctrl.onchange_year_column_dropdown, "value")
        self.value_column_ddown = ui.Dropdown(value="", options=[""], layout=control_layout)
        self.value_column_ddown.observe(self.ctrl.onchange_value_column_dropdown, "value")
        # -preview table widgets
        self._input_data_table_childrenpool = [
            ui.Box(children=[ui.Label(value="")]) for _ in range(33)  # Using 33 as cache size is random
        ]
        self.input_data_preview_tbl = ui.GridBox(
            children=self._input_data_table_childrenpool[:24],  # 24 because we assume the table dimension to be
            # 3 x 8 (the row number will stay the same, but the column number may vary)
            layout=ui.Layout(grid_template_columns="repeat(8, 1fr)"),
        )
        self.input_data_preview_tbl.add_class(CSS.PREVIEW_TABLE)

        self.output_data_preview_tbl = ui.GridBox(
            children=[
                ui.Box(children=[ui.Label(value="")]) for _ in range(24)
            ],  # 24 because of the 3 x 8 table dimension (invariant)
            layout=ui.Layout(grid_template_columns="repeat(8, 1fr"),
        )
        self.output_data_preview_tbl.add_class(CSS.PREVIEW_TABLE)
        # -page navigation widgets
        next_ = ui.Button(description="Next", layout=ui.Layout(align_self="flex-end", justify_self="flex-end"))
        next_.on_click(self.ctrl.onclick_next_from_page_2)
        previous = ui.Button(
            description="Previous", layout=ui.Layout(align_self="flex-end", justify_self="flex-end", margin="0px 8px")
        )
        previous.on_click(self.ctrl.onclick_previous_from_page_2)
        # Create specifications section
        # this section is separated from the page build below to avoid too many indentations
        label_layout = ui.Layout(width="205px")
        wrapper_layout = ui.Layout(overflow_y="hidden")  # prevent scrollbar from appearing on safari
        specifications_area = ui.VBox(  # Specification box
            children=[
                ui.GridBox(  # -Grid box for all specifications except for "Scenarios to ignore"
                    children=(
                        ui.HBox(
                            children=(ui.Label(value="Model name *", layout=label_layout), self.model_name_ddown),
                            layout=wrapper_layout,
                        ),
                        ui.HBox(
                            children=(ui.Label(value="Delimiter *", layout=label_layout), self.delimiter_ddown),
                            layout=wrapper_layout,
                        ),
                        ui.HBox(
                            children=(
                                ui.Label(value="Header is included *", layout=label_layout),
                                self.header_is_included_chkbox,
                            ),
                            layout=wrapper_layout,
                        ),
                        ui.HBox(
                            children=(
                                ui.Label(value="Number of initial lines to skip *", layout=label_layout),
                                self.lines_to_skip_txt,
                            ),
                            layout=wrapper_layout,
                        ),
                    ),
                    layout=ui.Layout(width="100%", grid_template_columns="auto auto", grid_gap="4px 56px"),
                ),
                ui.HBox(  # -Scenarios to ignore box
                    children=(
                        ui.Label(value="Scenarios to ignore", layout=label_layout),
                        self.scenarios_to_ignore_txt,
                    ),
                    layout=ui.Layout(margin="4px 0px 0px 0px"),
                ),
            ],
            layout=ui.Layout(padding="8px 0px 16px 0px"),
        )
        # Create page
        return ui.VBox(  # Page
            children=(
                ui.VBox(  # -Box to fill up the space above navigation buttons
                    children=(
                        ui.VBox(  # --Box for the page's main components
                            children=(
                                ui.HTML(value="<b>Specify the format of the input data</b>"),  # ---Title
                                specifications_area,  # ---Specifications area
                                ui.HTML(
                                    value="<b>Assign columns from the input data to the output data</b>"
                                ),  # ---Title
                                CSS.assign_class(
                                    ui.GridBox(  # --Column assignment table
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
                                ui.HTML(value="<b>Preview of the input data</b>"),
                                self.input_data_preview_tbl,  # --preview table
                                ui.HTML(value="<b>Preview of the output data</b>"),
                                self.output_data_preview_tbl,  # --preview table
                            ),
                            layout=ui.Layout(width="900px"),
                        ),
                    ),
                    layout=ui.Layout(flex="1", width="100%", justify_content="center", align_items="center"),
                ),
                ui.HBox(  # -Navigation buttons box
                    children=[previous, next_], layout=ui.Layout(justify_content="flex-end", width="100%")
                ),
            ),
            layout=ui.Layout(flex="1", width="100%", align_items="center", justify_content="center"),
        )

    def _build_integrity_checking_page(self) -> ui.Box:
        """Build the integrity checking page"""
        # Create the control widgets
        # - download buttons
        download_rows_field_issues_btn = ui.HTML(
            value=f"""
                <a
                    href="{str(self.model.structissuefile_path)}" 
                    download="{str(self.model.structissuefile_path.name)}"
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
                    href="{str(self.model.ignoredscenariofile_path)}" 
                    download="{str(self.model.ignoredscenariofile_path.name)}"
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
                    href="{str(self.model.duplicatesfile_path)}" 
                    download="{str(self.model.duplicatesfile_path.name)}"
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
                    href="{str(self.model.acceptedfile_path)}" 
                    download="{str(self.model.acceptedfile_path.name)}"
                    class="{CSS.ICON_BUTTON}"
                    style="line-height:36px;"
                    title=""
                >
                    <i class="fa fa-download" style="margin-left: 4px;"></i>
                </a>
            """
        )
        # - row summary labels
        self.rows_w_struct_issues_lbl = ui.Label(value="0")
        self.rows_w_ignored_scenario_lbl = ui.Label(value="0")
        self.duplicate_rows_lbl = ui.Label(value="0")
        self.accepted_rows_lbl = ui.Label(value="0")
        # - bad labels table
        _empty_row = """
            <tr>
                <td>-</td>
                <td>-</td>
                <td>-</td>
            <tr>
        """
        self.bad_labels_tbl.value = f"""
            <table>
                <thead>
                    <th>Label</th>
                    <th>Associated column</th>
                    <th>Fix</th>
                </thead>
                <tbody>
                    {_empty_row * 3}
                </tbody>
            </table>
            """
        self.bad_labels_tbl.add_class(CSS.BAD_LABELS_TABLE)
        # - unknown labels table
        self._unknown_labels_tbl_childrenpool = [
            ui.Box(children=[ui.Label(value="Label")]),
            ui.Box(children=[ui.Label(value="Associated column")]),
            ui.Box(children=[ui.Label(value="Closest Match")]),
            ui.Box(children=[ui.Label(value="Fix")]),
            ui.Box(children=[ui.Label(value="Override")]),
        ]
        from copy import deepcopy

        for index in range(10):
            dropdown = ui.Dropdown()
            # the following lambda return a callback that can be called by ipywidgets
            _get_dropdown_callback = lambda row_index: lambda change: self.ctrl.onchange_fix_dropdown(change, row_index)
            dropdown.observe(_get_dropdown_callback(index), "value")
            checkbox = ui.Checkbox(indent=False, value=False, description="")
            # the following lambda return a callback that can be called by ipywidgets
            _get_checkbox_callback = lambda row_index: lambda change: self.ctrl.onchange_override_checkbox(
                change, row_index
            )
            checkbox.observe(_get_checkbox_callback(index), "value")
            self._unknown_labels_tbl_childrenpool += [
                ui.Box(children=[ui.Label(value="-")]),
                ui.Box(children=[ui.Label(value="-")]),
                ui.Box(children=[ui.Label(value="-")]),
                ui.Box(children=[dropdown]),
                ui.Box(children=[checkbox]),
            ]
        self.unknown_labels_tbl.children = self._unknown_labels_tbl_childrenpool[:20]
        self.unknown_labels_tbl.add_class(CSS.UNKNOWN_LABELS_TABLE)
        # - page navigation buttons
        next_ = ui.Button(description="Next", layout=ui.Layout(align_self="flex-end", justify_self="flex-end"))
        next_.on_click(self.ctrl.onclick_next_from_page_3)
        previous = ui.Button(
            description="Previous", layout=ui.Layout(align_self="flex-end", justify_self="flex-end", margin="0px 8px")
        )
        previous.on_click(self.ctrl.onclick_previous_from_page_3)
        # Create page
        return ui.VBox(  # Page
            children=(
                ui.VBox(  # -Box to fill up the space above navigation buttons
                    children=(
                        ui.VBox(  # --Box for the page's main components
                            children=(
                                ui.HTML(value='<b style="line-height:13px; margin-bottom:4px;">Rows overview</b>'),
                                ui.HTML(
                                    value=(
                                        '<span style="line-height: 13px; color: var(--grey);">The'
                                        " table shows an overview of the uploaded data's rows. The"
                                        " rows can be downloaded to be analyzed.</span>"
                                    )
                                ),
                                ui.HBox(
                                    children=[
                                        CSS.assign_class(
                                            ui.GridBox(  # ----Bad rows overview table
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
                                                            ui.Label(
                                                                value="Number of rows containing an ignored scenario"
                                                            ),
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
                                        ui.VBox(
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
                                ui.HTML(
                                    value='<b style="line-height:13px; margin-bottom:4px;">Bad labels overview</b>'
                                ),
                                ui.HTML(
                                    value=(
                                        '<span style="line-height: 13px; color: var(--grey);">The table lists'
                                        " labels that are recognized by the program but do not adhere to the correct"
                                        " standard. They will be fixed automatically."
                                    )
                                ),
                                self.bad_labels_tbl,
                                ui.HTML(
                                    value=(
                                        '<b style="line-height:13px; margin: 20px 0px 4px;">Unknown labels overview</b>'
                                    )
                                ),
                                ui.HTML(
                                    value=(
                                        '<span style="line-height: 13px; color: var(--grey);">The table lists labels'
                                        " that are not recognized by the program. Please fix or override the labels,"
                                        " otherwise records containing them will be dropped."
                                    )
                                ),
                                self.unknown_labels_tbl,
                            ),
                            layout=ui.Layout(width="850px"),
                        ),
                    ),
                    layout=ui.Layout(flex="1", width="100%", justify_content="center", align_items="center"),
                ),
                ui.HBox(  # -Navigation buttons box
                    children=[previous, next_], layout=ui.Layout(justify_content="flex-end", width="100%")
                ),
            ),
            layout=ui.Layout(flex="1", width="100%", align_items="center", justify_content="center"),
        )

    def _build_plausibility_checking_page(self) -> ui.Box:
        # Control widgets
        value_tab_btn = ui.Button()
        value_tab_btn.on_click(self.ctrl.onclick_value_trends_tab)
        growth_tab_btn = ui.Button()
        growth_tab_btn.on_click(self.ctrl.onclick_growth_trends_tab)
        box_tab_btn = ui.Button()
        box_tab_btn.on_click(self.ctrl.onclick_box_plot_tab)
        self.valuetrends_tabelement = ui.Box(children=[ui.Label(value="Value trends"), value_tab_btn])
        self.valuetrends_tabelement.add_class(CSS.VISUALIZATION_TAB__ELEMENT)
        self.growthtrends_tabelement = ui.Box(children=[ui.Label(value="Growth trends"), growth_tab_btn])
        self.growthtrends_tabelement.add_class(CSS.VISUALIZATION_TAB__ELEMENT)
        self.boxplot_tabelement = ui.Box(children=[ui.Label(value="Box plot"), box_tab_btn])
        self.boxplot_tabelement.add_class(CSS.VISUALIZATION_TAB__ELEMENT)
        visualization_tab = CSS.assign_class(
            ui.GridBox(
                children=[
                    self.valuetrends_tabelement,
                    self.growthtrends_tabelement,
                    self.boxplot_tabelement,
                ]
            ),
            CSS.VISUALIZATION_TAB,
        )
        assert isinstance(visualization_tab, ui.GridBox)
        visualization_tab.children[0].add_class(CSS.VISUALIZATION_TAB__ELEMENT__ACTIVE)
        # Shared layouts
        _ddown_layout = ui.Layout(width="200px")
        _vis_output_layout = ui.Layout(
            margin="24px 0px 0px",
            justify_content="center",
            align_items="center",
            height="360px",
            width="100%",
            overflow="auto",
        )
        # value trends tab page
        self.valuetrends_scenario_ddown = ui.Dropdown(layout=_ddown_layout, options=self.model.uploaded_scenarios)
        self.valuetrends_scenario_ddown.observe(self.ctrl.onchange_valuetrends_scenario, "value")
        self.valuetrends_region_ddown = ui.Dropdown(layout=_ddown_layout, options=self.model.uploaded_regions)
        self.valuetrends_region_ddown.observe(self.ctrl.onchange_valuetrends_region, "value")
        self.valuetrends_variable_ddown = ui.Dropdown(layout=_ddown_layout, options=self.model.uploaded_variables)
        self.valuetrends_variable_ddown.observe(self.ctrl.onchange_valuetrends_variable, "value")
        visualize_value_btn = ui.Button(description="Visualize", layout=ui.Layout(margin="24px 0px 0px 0px"))
        visualize_value_btn.on_click(self.ctrl.onclick_visualize_value_trends)
        self.valuetrends_viz_output.layout = _vis_output_layout
        with self.valuetrends_viz_output:
            _, axes = plt.subplots(figsize=(PLOT_HEIGHT, PLOT_WIDTH))
            axes.set_xlabel("Year")
            axes.set_ylabel("Value")
            plt.title("Value Trends")
            plt.grid()
            plt.show()
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
        # growth trends tab page
        self.growthtrends_scenario_ddown = ui.Dropdown(layout=_ddown_layout, options=self.model.uploaded_scenarios)
        self.growthtrends_scenario_ddown.observe(self.ctrl.onchange_growthtrends_scenario, "value")
        self.growthtrends_region_ddown = ui.Dropdown(layout=_ddown_layout, options=self.model.uploaded_regions)
        self.growthtrends_region_ddown.observe(self.ctrl.onchange_growthtrends_region, "value")
        self.growthtrends_variable_ddown = ui.Dropdown(layout=_ddown_layout, options=self.model.uploaded_variables)
        self.growthtrends_variable_ddown.observe(self.ctrl.onchange_growthtrends_variable, "value")
        visualize_growth_btn = ui.Button(description="Visualize", layout=ui.Layout(margin="24px 0px 0px 0px"))
        visualize_growth_btn.on_click(self.ctrl.onclick_visualize_growth_trends)
        self.growthtrends_viz_output.layout = _vis_output_layout
        with self.growthtrends_viz_output:
            _, axes = plt.subplots(figsize=(PLOT_HEIGHT, PLOT_WIDTH))  # size in inches
            axes.set_xlabel("Year")
            axes.set_ylabel("Growth value")
            plt.title("Growth Rate Trends")
            plt.grid()
            plt.show()
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
        # box plot tab page
        self.boxplot_scenario_ddown = ui.Dropdown(layout=_ddown_layout, options=self.model.uploaded_scenarios)
        self.boxplot_region_ddown = ui.Dropdown(layout=_ddown_layout, options=self.model.uploaded_regions)
        self.boxplot_variable_ddown = ui.Dropdown(layout=_ddown_layout, options=self.model.uploaded_variables)
        self.boxplot_item_ddown = ui.Dropdown(layout=_ddown_layout, options=self.model.uploaded_items)
        self.boxplot_year_ddown = ui.Dropdown(layout=_ddown_layout, options=self.model.uploaded_items)
        visualize_box_btn = ui.Button(description="Visualize", layout=ui.Layout(margin="24px 0px 0px 0px"))
        visualize_box_btn.on_click(self.ctrl.onclick_visualize_box_plot)
        self.boxplot_viz_output.layout = _vis_output_layout
        with self.boxplot_viz_output:
            _, axes = plt.subplots(figsize=(PLOT_HEIGHT, PLOT_WIDTH))
            axes.boxplot([1, 2, 3, 4, 5, 6])  # Dummy data
            plt.title("Inter-model Box Plot (Work-in-progress)")
            plt.show()
            print("*The shown boxplot is just a sample")
        self.boxplot_tabcontent = ui.VBox(
            children=[
                ui.GridBox(
                    children=(
                        ui.HTML(value="1. Scenario"),
                        self.boxplot_scenario_ddown,
                        ui.HTML(value="2. Region"),
                        self.boxplot_region_ddown,
                        ui.HTML(value="3. Variable"),
                        self.boxplot_variable_ddown,
                        ui.HTML(value="4. Item"),
                        self.boxplot_item_ddown,
                        ui.HTML(value="5. Year"),
                        self.boxplot_year_ddown,
                    ),
                    layout=ui.Layout(
                        grid_template_columns="1fr 2fr 1fr 2fr 1fr 2fr", grid_gap="16px 16px", overflow_y="hidden"
                    ),
                ),
                visualize_box_btn,
                self.boxplot_viz_output,
            ],
            layout=ui.Layout(align_items="center", padding="24px 0px 0px 0px", overflow_y="hidden"),
        )
        self.boxplot_tabcontent.add_class(CSS.DISPLAY_MOD__NONE)
        # -page navigation widgets
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
        previous = ui.Button(
            description="Previous", layout=ui.Layout(align_self="flex-end", justify_self="flex-end", margin="0px 8px")
        )
        previous.on_click(self.ctrl.onclick_previous_from_page_4)
        # Create page
        return ui.VBox(  # Page
            children=(
                ui.VBox(  # -Box to fill up the space above navigation buttons
                    children=(
                        ui.VBox(  # --Box for the page's main components
                            children=(
                                ui.HBox(
                                    children=[
                                        ui.VBox(
                                            children=[
                                                ui.HTML(
                                                    value=(
                                                        '<b style="line-height:13px; margin-bottom:4px;">Plausibility'
                                                        " checking</b>"
                                                    )
                                                ),
                                                ui.HTML(
                                                    value=(
                                                        '<span style="line-height: 13px; color: var(--grey);">Visualize'
                                                        " the uploaded data and verify that it looks plausible"
                                                        " (Work-in-progress).</span>"
                                                    )
                                                ),
                                            ],
                                            layout=ui.Layout(height="32px"),
                                        ),
                                        visualization_tab,
                                    ],
                                    layout=ui.Layout(
                                        align_items="center", justify_content="space-between", width="100%"
                                    ),
                                ),
                                self.valuetrends_tabcontent,
                                self.growthtrends_tabcontent,
                                self.boxplot_tabcontent,
                            ),
                            layout=ui.Layout(width="900px", align_items="center"),
                        ),
                    ),
                    layout=ui.Layout(flex="1", width="100%", justify_content="center", align_items="center"),
                ),
                ui.HBox(
                    children=[previous, submit], layout=ui.Layout(justify_content="flex-end", width="100%")
                ),  # -buttons box
            ),
            layout=ui.Layout(flex="1", width="100%", align_items="center", justify_content="center"),
        )
