from __future__ import annotations
from typing import Union  # Delay the evaluation of undefined types
from threading import Timer

import ipywidgets as ui
from IPython.core.display import display
from IPython.core.display import HTML


DARK_BLUE = "#1E3A8A"
LIGHT_GREY = "#D3D3D3"


class Icon:
    """Namespace for icon constants"""

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
    SUCCESS = "success"
    WARNING = "warning"
    INFO = "info"

    _VARIANTS = [ERROR, SUCCESS, WARNING, INFO]


class CSS:
    """Namespace for CSS classes declared in style.html"""

    DISPLAY_MOD__NONE = "c-display-mod--none"
    COLOR_MOD__WHITE = "c-color-mod--white"
    COLOR_MOD__BLACK = "c-color-mod--black"
    NOTIFICATION = "c-notification"
    NOTIFICATION__SHOW = "c-notification--show"
    NOTIFICATION__SUCCESS = "c-notification--success"
    NOTIFICATION__INFO = "c-notification--info"
    NOTIFICATION__WARNING = "c-notification--warning"
    NOTIFICATION__ERROR = "c-notification--error"


# pyright: reportGeneralTypeIssues=false
class View:
    def __init__(self):
        # Import MVC classes here to prevent circular import problem
        from .controller import Controller
        from .model import Model

        # MVC objects self.model: Model
        self.model: Model
        self.ctrl: Controller

        # Page container & other app pages
        self.page_container: ui.Box
        self.file_upload_page: ui.Box
        self.data_specification_page: ui.Box
        self.integrity_checking_page: ui.Box
        self.plausibility_checking_page: ui.Box

        self.stepper: ui.Box
        self.notification: ui.Box
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
        display(HTML(filename="style.html"))
        display(app_container)

        # Embed app model in Javascript context
        display(HTML(f"<script> APP_MODEL = {self.model.javascript_app_model()}</script>"))
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
        self.notification.add_class("c-notification")
        # Create header bar
        header_bar = ui.HTML(APP_TITLE)
        header_bar.add_class("c-header-bar")
        # Create stepper
        stepper_children = []
        for i in range(0, NUM_OF_PAGES):
            page_number = ui.HTML(value=str(i + 1))
            page_number.add_class("c-stepper__number")  # Available modifiers are current, active, inactive
            page_number.add_class("c-stepper__number--current" if i == 0 else "c-stepper__number--inactive")

            page_title = ui.HTML(PAGE_TITLES[i])  # Available modifiers are active, inactive
            page_title.add_class("c-stepper__title--active" if i == 0 else "c-stepper__title--inactive")
            separator = ui.HTML("<hr width=48px/>")  # Available modifiers are active, inactive
            separator.add_class("c-stepper__separator--inactive")

            is_last_page = i == NUM_OF_PAGES - 1
            stepper_children += [page_number, page_title] if is_last_page else [page_number, page_title, separator]
        self.stepper = ui.HBox(stepper_children)
        self.stepper.add_class("c-stepper")

        # Create app pages & page container
        self.file_upload_page = self._build_file_upload_page()
        self.data_specification_page = self._build_data_specification_page()
        self.integrity_checkgin_page = self._build_integrity_checking_page()
        self.integrity_checkgin_page = self._build_plausibility_checking_page()
        self.page_container = ui.Box(
            [self.file_upload_page], layout=ui.Layout(flex="1", width="100%")  # page container stores the current page
        )

        app = ui.VBox(  # app container
            [
                self.notification,
                header_bar,  # -header bar
                ui.VBox(  # -body container
                    children=[self.stepper, self.page_container],  # --stepper, page container
                    layout=ui.Layout(flex="1", align_items="center", padding="36px 48px"),
                ),
            ],
        )
        app.add_class("app-container")
        return app

    counter = 0

    def show_notification(self, variant: str, content: str) -> None:
        """Display a notification to the user"""
        assert variant in Notification._VARIANTS

        # Cancel existing timer if it's still running
        self.notification_timer.cancel()

        # Reset the notification's DOM classes
        # This is important because we implement a clickaway listener in JS which will remove a DOM class from the
        # notification view without informing the notification model. Doing this will reset the DOM classes that the
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
                ui.HTML("<div class=c-text-grey>Browse files from your computer</div>"),
            ]
        )
        ua_background.add_class("c-upload-area__background")
        ua_overlay = ui.HTML(
            """
            <input class="c-upload-area__file-uploader" type="file" title="Click to browse" accept=".csv">
            """
        )
        ua_overlay.add_class("c-upload-area__overlay")
        self.ua_file_label = ui.Label("")
        self.ua_file_label.add_class("c-upload-area__uploaded-file-name")
        self.ua_file_label.observe(self.ctrl.onchange_ua_file_label, "value")
        self.model.update_javascript_app_model("ua_file_label_model_id", self.ua_file_label.model_id)
        upload_area = ui.Box(
            [ua_background, ua_overlay, self.ua_file_label],
            layout=ui.Layout(margin="32px 0px"),
        )
        upload_area._dom_classes = ["c-upload-area"]

        # Create a box to show that there's no file uploaded or to show the the uploaded file's name
        # -Create snackbar to tell the user that no file has been uploaded
        no_file_uploaded = ui.HTML(
            '<div style="width: 365px; line-height: 36px; border-radius: 4px; padding: 0px 16px;'
            ' background: var(--light-grey); color: white;"> No file uploaded </div>'
        )
        # -Create snackbar to show the uploaded file's name
        uploaded_file_name = ui.Label("<filename>")
        uploaded_file_name.add_class("c-snackbar__text")
        x_button = ui.Button(icon="times")
        x_button.add_class("c-icon-button")
        x_button.on_click(self.ctrl.onclick_remove_file)
        uploaded_file_snackbar = ui.Box(
            [
                uploaded_file_name,
                x_button,
            ],
        )
        uploaded_file_snackbar.add_class("c-snackbar")
        uploaded_file_snackbar.add_class("c-display-mod--none")  # By default this snackbar is hidden
        # -Create the box
        self.uploaded_file_name_box = ui.Box([no_file_uploaded, uploaded_file_snackbar])

        # Buttons
        download_button = ui.HTML(
            """
                <a
                    href="SampleData.csv" 
                    download="SampleData.csv"
                    class="btn p-Widget jupyter-widgets jupyter-button widget-button mod-info" 
                    title=""
                >
                    Download
                    <i class="fa fa-download" style="margin-left: 4px;"></i>
                </a>
            """
        )
        next_button = ui.Button(
            description="Next", layout=ui.Layout(align_self="flex-end", justify_self="flex-end")
        )
        next_button.on_click(self.ctrl.onclick_next_from_page_1)
        return ui.VBox(  # page
            [
                ui.VBox(  # -container to fill up the space above navigation button area
                    [
                        ui.VBox(  # --instruction container
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
                ui.VBox([next_button], layout=ui.Layout(align_self="flex-end")),  # -container for navgation button
            ],
            layout=ui.Layout(flex="1", width="100%", align_items="center", justify_content="center"),
        )

    def _build_data_specification_page(self) -> ui.Box:
        return ui.Box()

    def _build_integrity_checking_page(self) -> ui.Box:
        return ui.Box()

    def _build_plausibility_checking_page(self) -> ui.Box:
        return ui.Box()
