from __future__ import annotations  # Delay the evaluation of undefined types

import ipywidgets as ui
from IPython.core.display import display
from IPython.core.display import HTML


DARK_BLUE = "#1E3A8A"
LIGHT_GREY = "#D3D3D3"


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
        # Widgets that controller needs to access

        # Widgets that controller does not need to access but still needs to be manipulated
        self.stepper: ui.Box
        self.next_button: ui.Button
        self.uploaded_file_snackbar: ui.Box

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
                header_bar,  # -header bar
                ui.VBox(  # -body container
                    children=[self.stepper, self.page_container],  # --stepper, page container
                    layout=ui.Layout(flex="1", align_items="center", padding="36px 48px"),
                ),
            ],
        )
        app.add_class("app-container")
        return app

    def _build_file_upload_page(self) -> ui.Box:
        """Build the file upload page"""
        INSTRUCTION = '<h3 style="margin: 0px;">Upload file to be processed</h3>'
        SUB_INSTRUCTION = (
            '<span style="font-size: 15px; line-height: 20px; margin: 0px; color: var(--grey);">'
            "File should be in CSV format</span>"
        )
        UPLOADED_FILE = '<div style="width: 125px; line-height: 36px;">Uploaded file</div>'
        SAMPLE_FILE = '<div style="width: 125px; line-height: 36px;">Sample file</div>'
        NO_FILE_UPLOADED = (
            '<div style="width: 365px; line-height: 36px; border-radius: 4px; padding: 0px 16px;'
            ' background: var(--light-grey); color: white;"> No files uploaded </div>'
        )

        # Create file upload area / ua
        ua_background = ui.Box(
            [
                ui.HTML('<img src="upload_file.svg" width="80px" height="800px"/>'),
                ui.HTML("<div class=c-text-grey>Browse files from your computer</div>"),
            ]
        )
        ua_background.add_class("c-upload-area__background")
        ua_overlay = ui.HTML(
            # title=" " is set to prevent tooltip from showing upon hover
            """
            <input class="c-upload-area__file-uploader" type="file" title=" " accept=".csv">
            """
        )
        ua_overlay.add_class("c-upload-area__overlay")
        ua_file_name_label = ui.Label("No file uploaded")
        ua_file_name_label.add_class("c-upload-area__uploaded-file-name")
        self.model.update_javascript_app_model("ua_label_model_id", ua_file_name_label.model_id)

        upload_area = ui.Box(
            [ua_background, ua_overlay, ua_file_name_label],
            layout=ui.Layout(margin="32px 0px"),
        )
        upload_area._dom_classes = ["c-upload-area"]

        # Create snackbar to show uploaded file
        uploaded_file_name = ui.Label("No file uploaded")
        ui.jslink((uploaded_file_name, "value"), (ua_file_name_label, "value"))
        uploaded_file_name.add_class("c-snackbar__text")

        x_button = ui.Button(icon="times")
        x_button.add_class("c-icon-button")
        self.uploaded_file_snackbar = ui.Box(
            [
                uploaded_file_name,
                x_button,
            ],
        )
        self.uploaded_file_snackbar.add_class("c-snackbar")

        # Buttons
        download_button = ui.Button(description="Download", icon="download", button_style="info")
        download_button.on_click(self.ctrl.onclick_download)
        self.next_button = ui.Button(
            description="Next", disabled=True, layout=ui.Layout(align_self="flex-end", justify_self="flex-end")
        )

        return ui.VBox(  # page
            [
                ui.VBox(  # -container to fill up the space above navigation button area
                    [
                        ui.VBox(  # --instruction container
                            layout=ui.Layout(width="500px"), children=[ui.HTML(INSTRUCTION), ui.HTML(SUB_INSTRUCTION)]
                        ),
                        upload_area,  # --upload area
                        ui.HBox(  # --uploaded file container
                            [ui.HTML(UPLOADED_FILE), ui.HTML(NO_FILE_UPLOADED)],
                            layout=ui.Layout(width="500px", margin="0px 0px 4px 0px"),
                        ),
                        ui.HBox(  # --sample file container
                            [ui.HTML(SAMPLE_FILE), download_button], layout=ui.Layout(width="500px")
                        ),
                    ],
                    layout=ui.Layout(flex="1", justify_content="center"),
                ),
                ui.VBox([self.next_button], layout=ui.Layout(align_self="flex-end")),  # -container for navgation button
            ],
            layout=ui.Layout(flex="1", width="100%", align_items="center", justify_content="center"),
        )

    def _build_data_specification_page(self) -> ui.Box:
        return ui.Box()

    def _build_integrity_checking_page(self) -> ui.Box:
        return ui.Box()

    def _build_plausibility_checking_page(self) -> ui.Box:
        return ui.Box()
