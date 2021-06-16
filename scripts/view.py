from __future__ import annotations

import math
from ipywidgets.widgets.domwidget import DOMWidget
from ipywidgets.widgets.widget_layout import Layout
from numpy import number
from scripts.model import JSAppModel
from typing import Optional, Union  # Delay the evaluation of undefined types
from threading import Timer

import ipywidgets as ui
from IPython.core.display import display
from IPython.core.display import HTML


DARK_BLUE = "#1E3A8A"
LIGHT_GREY = "#D3D3D3"


class Icon:
    """Namespace for icon html objects"""

    WARNING = ui.HTML(
        """
        <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" fill="currentColor" class="bi bi-exclamation-triangle" viewBox="0 0 18 18"
            style="color: black; margin-right: 4px;" 
        >
            <path d="M7.938 2.016A.13.13 0 0 1 8.002 2a.13.13 0 0 1 .063.016.146.146 0 0 1 .054.057l6.857 11.667c.036.06.035.124.002.183a.163.163 0 0 1-.054.06.116.116 0 0 1-.066.017H1.146a.115.115 0 0 1-.066-.017.163.163 0 0 1-.054-.06.176.176 0 0 1 .002-.183L7.884 2.073a.147.147 0 0 1 .054-.057zm1.044-.45a1.13 1.13 0 0 0-1.96 0L.165 13.233c-.457.778.091 1.767.98 1.767h13.713c.889 0 1.438-.99.98-1.767L8.982 1.566z"/>
            <path d="M7.002 12a1 1 0 1 1 2 0 1 1 0 0 1-2 0zM7.1 5.995a.905.905 0 1 1 1.8 0l-.35 3.507a.552.552 0 0 1-1.1 0L7.1 5.995z"/>
        </svg>
        """
    )
    ERROR = ui.HTML(
        """
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
        """
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


class CSS:
    """Namespace for CSS classes declared in style.html and used in Python"""

    APP = "c-app-container"
    COLOR_MOD__WHITE = "c-color-mod--white"
    COLOR_MOD__BLACK = "c-color-mod--black"
    COLOR_MOD__GREY = "c-color-mod--grey"
    COLUMN_ASSIGNMENT_TABLE = "c-column-assignment-table"
    DISPLAY_MOD__NONE = "c-display-mod--none"
    FILENAME_SNACKBAR = "c-filename-snackbar"
    FILENAME_SNACKBAR__TEXT = "c-filename-snackbar__text"
    HEADER_BAR = "c-header-bar"
    ICON_BUTTON = "c-icon-button"
    NOTIFICATION = "c-notification"
    NOTIFICATION__ERROR = "c-notification--error"
    NOTIFICATION__INFO = "c-notification--info"
    NOTIFICATION__SHOW = "c-notification--show"
    NOTIFICATION__SUCCESS = "c-notification--success"
    NOTIFICATION__WARNING = "c-notification--warning"
    PREVIEW_TABLE = "c-preview-table"
    STEPPER = "c-stepper"
    STEPPER__NUMBER = "c-stepper__number"
    STEPPER__NUMBER__ACTIVE = "c-stepper__number--active"
    STEPPER__NUMBER__CURRENT = "c-stepper__number--current"
    STEPPER__NUMBER__INACTIVE = "c-stepper__number--inactive"
    STEPPER__SEPARATOR__ACTIVE = "c-stepper__separator--active"
    STEPPER__SEPARATOR__INACTIVE = "c-stepper__separator--inactive"
    STEPPER__TITLE__ACTIVE = "c-stepper__title--active"
    STEPPER__TITLE__INACTIVE = "c-stepper__title--inactive"
    UA = "c-upload-area"
    UA__BACKGROUND = "c-upload-area__background"
    UA__FILE_UPLOADER = "c-upload-area__file-uploader"
    UA__OVERLAY = "c-upload-area__overlay"
    UA__FILE_LABEL = "c-upload-area__file-label"

    @classmethod
    def assign_class(cls, widget: DOMWidget, class_name: str) -> DOMWidget:
        # Get attribute names by filtering out method names from __dict__.keys()
        attribute_names = [name for name in cls.__dict__.keys() if name[:1] != "__"]
        defined_css_classes = [getattr(cls, name) for name in attribute_names]
        assert class_name in defined_css_classes
        assert isinstance(widget, DOMWidget)
        widget.add_class(class_name)
        return widget


# pyright: reportGeneralTypeIssues=false
class View:
    def __init__(self):
        # Import MVC classes here to prevent circular import problem
        from .controller import Controller
        from .model import Model

        # MVC objects self.model: Model
        self.model: Model
        self.ctrl: Controller

        # Main app's helper widgets
        self.page_container: ui.Box = None
        self.page_stepper: ui.Box = None
        self.notification: ui.Box = None
        self.notification_timer: Timer = Timer(0.0, None)
        # Widgets in file upload page that needs to be manipulated
        self.ua_file_label: ui.Label  # ua here stands for "upload area"
        self.uploaded_file_name_box: ui.Box

    def intro(self, model: Model, ctrl: Controller) -> None:  # type: ignore # noqa
        """Introduce MVC modules to each other"""
        self.model = model
        self.ctrl = ctrl

    def display(self) -> None:
        """Build and show notebook user interface"""
        app_container = self.build()
        # Display the appropriate html files and our ipywidgets app
        display(HTML(filename="style.html"))
        display(app_container)
        # Embed Javascript app model in Javascript context
        javascript_model: JSAppModel = self.model.javascript_model
        display(HTML(f"<script> APP_MODEL = {javascript_model.serialize()}</script>"))
        display(HTML(filename="script.html"))

    def build(self) -> ui.Box:
        """Build the application"""
        # Constants
        APP_TITLE = "AgMIP Model Submission Pipeline"
        PAGE_TITLES = ["File Upload", "Data Specification", "Integrity Checking", "Plausibility Checking"]
        NUM_OF_PAGES = 4
        # Create notification widget
        notification_text = ui.Label("")
        self.notification = ui.HBox(children=(Icon.SUCCESS, notification_text))
        self.notification.add_class(CSS.NOTIFICATION)
        # Create header bar
        header_bar = ui.HTML(APP_TITLE)
        header_bar.add_class(CSS.HEADER_BAR)
        # Create stepper
        stepper_children = []
        for i in range(0, NUM_OF_PAGES):
            page_number = ui.HTML(value=str(i + 1))
            page_number.add_class(CSS.STEPPER__NUMBER)
            page_number.add_class(CSS.STEPPER__NUMBER__CURRENT if i == 0 else CSS.STEPPER__NUMBER__INACTIVE)

            page_title = ui.HTML(PAGE_TITLES[i])
            page_title.add_class(CSS.STEPPER__TITLE__ACTIVE if i == 0 else CSS.STEPPER__TITLE__INACTIVE)
            separator = ui.HTML("<hr width=48px/>")
            separator.add_class(CSS.STEPPER__SEPARATOR__INACTIVE)

            is_last_page = i == NUM_OF_PAGES - 1
            stepper_children += [page_number, page_title] if is_last_page else [page_number, page_title, separator]
        self.page_stepper = ui.HBox(stepper_children)
        self.page_stepper.add_class(CSS.STEPPER)
        # Create app pages & page container
        self.page_container = ui.Box(
            [
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
            [
                self.notification,
                header_bar,  # -header bar
                ui.VBox(  # -body container
                    children=[self.page_stepper, self.page_container],  # --page stepper, page container
                    layout=ui.Layout(flex="1", align_items="center", padding="36px 48px"),
                ),
            ],
        )
        app.add_class(CSS.APP)
        return app

    counter = 0

    def show_notification(self, variant: str, content: str) -> None:
        """Display a notification to the user"""
        assert variant in Notification._VARIANTS

        # Cancel existing timer if it's still running
        self.notification_timer.cancel()

        # Reset the notification's DOM classes
        # This is important because we implement a clickaway listener in JS which removes a DOM class from the
        # notification view without notifying the notification model. Doing this will reset the DOM classes that the
        # notification models in both server-side & client-side are maintaining
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
        self.notification_timer = Timer(3.0, self.notification.remove_class, args=[CSS.NOTIFICATION__SHOW])
        self.notification_timer.start()

    def switch_page(self, page_number: int) -> None:
        """Show the next page"""
        assert page_number > 0 and page_number <= len(self.page_container.children)
        # Hide all pages
        for page in self.page_container.children:
            assert isinstance(page, ui.Box)
            page.add_class(CSS.DISPLAY_MOD__NONE)
        # Show the requested page
        page_number = page_number - 1
        page: ui.Box = self.page_container.children[page_number]
        page.remove_class(CSS.DISPLAY_MOD__NONE)
        # Change the number element with the "current" modifier to be "active"
        for child_element in self.page_stepper.children:
            assert isinstance(child_element, ui.DOMWidget)
            if CSS.STEPPER__NUMBER__CURRENT in child_element._dom_classes:
                child_element._dom_classes = (CSS.STEPPER__NUMBER, CSS.STEPPER__NUMBER__ACTIVE)
        # Update the stepper elements belonging to the current page
        # Format of page stepper's children = [number el, title el, separator el, ..., number el, title el]
        number_element = self.page_stepper.children[page_number * 3 + 0]
        title_element = self.page_stepper.children[page_number * 3 + 1]
        assert isinstance(number_element, ui.DOMWidget)
        assert isinstance(title_element, ui.DOMWidget)
        number_element._dom_classes = (CSS.STEPPER__NUMBER, CSS.STEPPER__NUMBER__CURRENT)
        title_element._dom_classes = (CSS.STEPPER__TITLE__ACTIVE,)
        # If the current page "just" become active, then its left separator would still be inactive, so activate it
        if page_number > 0:
            separator_element = self.page_stepper.children[page_number * 3 - 1]
            assert isinstance(separator_element, DOMWidget)
            separator_element._dom_classes = (CSS.STEPPER__SEPARATOR__ACTIVE,)

    def update_switch_page(self):
        pass
        """
        self.model.guessed_model_name
        self.model.guessed_delimeter
        self.model.guessed_header_inclusion
        self.model.guessed_number_of_lines_to_skip
        self.model.guessed_model_name
        self.model.guessed_sector_column
        self.model.guessed_sector_column
        self.model.columns 
        self.model.input_data_preview_table
        self.model.output_data_preview_table
        """

    def update_file_upload_page(self, uploaded_file_name: Union[str, None]) -> None:
        """
        File upload page has two states:
        1) when file was uploaded
        2) when file was not uploaded yet / uploaded file is removed

        To display state 2), pass a None as argument
        """
        children: tuple(ui.HTML, ui.Box) = self.uploaded_file_name_box.children
        no_file_uploaded_widget = children[0]
        file_uploaded_widget = children[1]

        if uploaded_file_name:
            no_file_uploaded_widget.add_class(CSS.DISPLAY_MOD__NONE)
            file_uploaded_widget.remove_class(CSS.DISPLAY_MOD__NONE)
            children: tuple(ui.Label, ui.Button) = file_uploaded_widget.children
            label_widget = children[0]
            label_widget.value = uploaded_file_name
        else:
            file_uploaded_widget.add_class(CSS.DISPLAY_MOD__NONE)
            no_file_uploaded_widget.remove_class(CSS.DISPLAY_MOD__NONE)

        # Reset the hidden filename value
        self.ua_file_label.value = ""

    def _build_file_upload_page(self) -> ui.Box:
        """Build the file upload page"""
        INSTRUCTION = '<h3 style="margin: 0px;">Upload file to be processed</h3>'
        SUB_INSTRUCTION = (
            '<span style="font-size: 15px; line-height: 20px; margin: 0px; color: var(--grey);">'
            "File should be in CSV format</span>"
        )
        UPLOADED_FILE = '<div style="width: 125px; line-height: 36px;">Uploaded file</div>'
        SAMPLE_FILE = '<div style="width: 125px; line-height: 36px;">Sample file</div>'

        # Create file upload area / ua
        ua_background = ui.Box(
            [
                ui.HTML('<img src="upload_file.svg" width="80px" height="800px"/>'),
                ui.HTML(f'<div class="{CSS.COLOR_MOD__GREY}"">Browse files from your computer</div>'),
            ]
        )
        ua_background.add_class(CSS.UA__BACKGROUND)
        ua_overlay = ui.HTML(
            f"""
            <input class="{CSS.UA__FILE_UPLOADER}" type="file" title="Click to browse" accept=".csv">
            """
        )
        ua_overlay.add_class(CSS.UA__OVERLAY)
        self.ua_file_label = ui.Label("")
        self.ua_file_label.add_class(CSS.UA__FILE_LABEL)
        self.ua_file_label.observe(self.ctrl.onchange_ua_file_label, "value")
        # Store the model id of file label in the js model (so that the label can be manipulated within js context)
        javascript_model: JSAppModel = self.model.javascript_model
        javascript_model.ua_file_label_model_id = self.ua_file_label.model_id
        upload_area = ui.Box(
            [ua_background, ua_overlay, self.ua_file_label],
            layout=ui.Layout(margin="32px 0px"),
        )
        upload_area._dom_classes = [CSS.UA]

        # Create a box to show that there's no file uploaded or to show the the uploaded file's name
        # -Create snackbar to tell the user that no file has been uploaded
        no_file_uploaded = ui.HTML(
            '<div style="width: 365px; line-height: 36px; border-radius: 4px; padding: 0px 16px;'
            ' background: var(--light-grey); color: white;"> No file uploaded </div>'
        )
        # -Create snackbar to show the uploaded file's name
        uploaded_file_name = ui.Label("")
        uploaded_file_name.add_class(CSS.FILENAME_SNACKBAR__TEXT)
        x_button = ui.Button(icon="times")
        x_button.add_class(CSS.ICON_BUTTON)
        x_button.on_click(self.ctrl.onclick_remove_file)
        uploaded_file_snackbar = ui.Box(
            [
                uploaded_file_name,
                x_button,
            ],
        )
        uploaded_file_snackbar.add_class(CSS.FILENAME_SNACKBAR)
        uploaded_file_snackbar.add_class(CSS.DISPLAY_MOD__NONE)  # By default this snackbar is hidden
        # -Create the box
        self.uploaded_file_name_box = ui.Box([no_file_uploaded, uploaded_file_snackbar])

        # Buttons
        download_button = ui.HTML(
            """
                <a
                    href="SampleData.csv" 
                    download="SampleData.csv"
                    class="btn p-Widget jupyter-widgets jupyter-button widget-button mod-danger" 
                    title=""
                >
                    Download
                    <i class="fa fa-download" style="margin-left: 4px;"></i>
                </a>
            """
        )
        next_button = ui.Button(description="Next", layout=ui.Layout(align_self="flex-end", justify_self="flex-end"))
        next_button.on_click(self.ctrl.onclick_next_from_page_1)
        return ui.VBox(  # page
            [
                ui.VBox(  # -container to fill up the space above navigation buttons
                    [
                        ui.VBox(  # --instructions container
                            layout=ui.Layout(width="500px"), children=[ui.HTML(INSTRUCTION), ui.HTML(SUB_INSTRUCTION)]
                        ),
                        upload_area,  # --upload area
                        ui.HBox(  # --uploaded file container
                            [ui.HTML(UPLOADED_FILE), self.uploaded_file_name_box],
                            layout=ui.Layout(width="500px", margin="0px 0px 4px 0px"),
                        ),
                        ui.HBox(  # --sample file container
                            [ui.HTML(SAMPLE_FILE), download_button], layout=ui.Layout(width="500px")
                        ),
                    ],
                    layout=ui.Layout(flex="1", justify_content="center"),
                ),
                ui.HBox([next_button], layout=ui.Layout(align_self="flex-end")),  # -navigation button box
            ],
            layout=ui.Layout(flex="1", width="100%", align_items="center", justify_content="center"),
        )

    def _build_data_specification_page(self) -> ui.Box:

        # Create all control widgets in this page
        control_layout = ui.Layout(flex="1 1", max_width="100%", display="flex")
        model_name_dropdown = ui.Dropdown(layout=control_layout)
        header_included_select = ui.Checkbox(indent=False, value=False, description="", layout=control_layout)
        skip_lines_text = ui.Text(layout=control_layout)
        delimeter_text = ui.Text(layout=control_layout)
        ignore_scenarios_text = ui.Textarea(
            placeholder="Enter comma-separated scenario values", layout=ui.Layout(flex="1", height="66px")
        )
        model_name_label = ui.Label("<model name>")
        scenario_column_dropdown = ui.Dropdown(layout=control_layout)
        region_column_dropdown = ui.Dropdown(layout=control_layout)
        variable_column_dropdown = ui.Dropdown(layout=control_layout)
        item_column_dropdown = ui.Dropdown(layout=control_layout)
        unit_column_dropdown = ui.Dropdown(layout=control_layout)
        year_column_dropdown = ui.Dropdown(layout=control_layout)
        value_column_dropdown = ui.Dropdown(layout=control_layout)
        next_ = ui.Button(description="Next", layout=ui.Layout(align_self="flex-end", justify_self="flex-end"))
        previous = ui.Button(
            description="Previous", layout=ui.Layout(align_self="flex-end", justify_self="flex-end", margin="0px 8px")
        )
        # Create specifications grid layout
        label_layout = ui.Layout(width="205px")
        specifications_area = ui.VBox(  # Specification box
            (
                ui.GridBox(  # -Grid box for all specifications except for "Scenarios to ignore"
                    (
                        ui.HBox((ui.Label("Model name *", layout=label_layout), model_name_dropdown)),
                        ui.HBox((ui.Label("Number of initial lines to skip *", layout=label_layout), skip_lines_text)),
                        ui.HBox((ui.Label("Header is included *", layout=label_layout), header_included_select)),
                        ui.HBox((ui.Label("Delimeter *", layout=label_layout), delimeter_text)),
                    ),
                    layout=ui.Layout(width="100%", grid_template_columns="auto auto", grid_gap="4px 56px"),
                ),
                ui.HBox(  # -Scenarios to ignore box
                    (ui.Label("Scenarios to ignore", layout=label_layout), ignore_scenarios_text),
                    layout=ui.Layout(margin="4px 0px 0px 0px"),
                ),
            ),
            layout=ui.Layout(padding="8px 0px 16px 0px"),
        )

        page = ui.VBox(  # Page
            (
                ui.VBox(  # -Box to fill up the space above navigation buttons
                    (
                        ui.VBox(  # --Box for the page's main components
                            (
                                ui.HTML("<b>Specifications</b>"),  # ---Title
                                specifications_area,  # ---Specifications area
                                ui.HTML("<b>Assign columns from the uploaded data to the output data</b>"),  # ---Title
                                CSS.assign_class(
                                    ui.GridBox(  # --Column assignment table
                                        (
                                            ui.Box((ui.Label("Model"),)),
                                            ui.Box((ui.Label("Scenario"),)),
                                            ui.Box((ui.Label("Region"),)),
                                            ui.Box((ui.Label("Variable"),)),
                                            ui.Box((ui.Label("Item"),)),
                                            ui.Box((ui.Label("Unit"),)),
                                            ui.Box((ui.Label("Year"),)),
                                            ui.Box((ui.Label("Value"),)),
                                            ui.Box((model_name_label,)),
                                            scenario_column_dropdown,
                                            region_column_dropdown,
                                            variable_column_dropdown,
                                            item_column_dropdown,
                                            unit_column_dropdown,
                                            year_column_dropdown,
                                            value_column_dropdown,
                                        )
                                    ),
                                    CSS.COLUMN_ASSIGNMENT_TABLE,
                                ),
                                ui.HTML("<b>Preview of uploaded data</b>"),
                                CSS.assign_class(
                                    ui.GridBox(  # --Column assignment table
                                        list(ui.Label("") for i in range(32)),
                                        layout=ui.Layout(grid_template_columns="repeat(8, 1fr)"),
                                    ),
                                    CSS.PREVIEW_TABLE,
                                ),
                                ui.HTML("<b>Preview of output data</b>"),
                                CSS.assign_class(
                                    ui.GridBox(  # --Column assignment table
                                        list(ui.Label("") for i in range(32)),
                                        layout=ui.Layout(grid_template_columns="repeat(8, 1fr"),
                                    ),
                                    CSS.PREVIEW_TABLE,
                                ),
                            ),
                            layout=ui.Layout(width="900px"),
                        ),
                    ),
                    layout=ui.Layout(flex="1", width="100%", justify_content="center", align_items="center"),
                ),
                ui.HBox(  # -Navigation buttons box
                    [previous, next_], layout=ui.Layout(justify_content="flex-end", width="100%")
                ),
            ),
            layout=ui.Layout(flex="1", width="100%", align_items="center", justify_content="center"),
        )
        return page

    def _build_integrity_checking_page(self) -> ui.Box:
        return ui.Box()

    def _build_plausibility_checking_page(self) -> ui.Box:
        return ui.Box()
