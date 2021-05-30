from __future__ import annotations
from re import M  # Delay the evaluation of undefined types

import ipywidgets as ui
from IPython.core.display import display

ui.FileUpload

DARK_BLUE = "#1E3A8A"
LIGHT_GREY = "#D3D3D3"


ui.Button().add_traits()

# pyright: reportGeneralTypeIssues=false
class View:
    def __init__(self):
        # Import MVC classes here to prevent circular import problem
        from .controller import Controller
        from .model import Model

        # MVC objects
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

    def intro(self, model: Model, ctrl: Controller) -> None:  # type: ignore
        """Introduce MVC modules to each other"""
        self.model = model
        self.ctrl = ctrl

    def display(self) -> None:
        """Build and show notebook user interface"""
        app_container = self.build()
        display(app_container)

    def build(self) -> ui.Box:
        """Build the application"""
        # Constants
        APP_TITLE = "AgMIP Model Submission Pipeline"
        PAGE_TITLES = ["File Upload", "Data Specification", "Integrity Checking", "Plausibility Checking"]
        NUM_OF_PAGES = 4

        # High level components
        app_container = ui.VBox()
        header_bar = ui.HTML(APP_TITLE)
        body_container = ui.VBox()

        # Widgets to manage app pages
        self.stepper = ui.HBox()
        self.page_container = ui.Box()
        self.file_upload_page = self._build_file_upload_page()
        self.data_specification_page = self._build_data_specification_page()
        self.integrity_checkgin_page = self._build_integrity_checking_page()
        self.integrity_checkgin_page = self._build_plausibility_checking_page()

        # Assign layouts & styling
        app_container.layout = ui.Layout(
            width="100%", height="912px", border="1px solid " + DARK_BLUE, padding="0px 0px"
        )
        header_bar.add_class("c-header-bar")
        body_container.layout = ui.Layout(flex="1", align_items="center", padding="36px 48px")
        self.page_container.layout = ui.Layout(flex="1", width="100%")
        self.stepper.add_class("c-stepper")

        # Assign children widgets
        app_container.children = [header_bar, body_container]
        body_container.children = [self.stepper, self.page_container]
        self.page_container.children = [self.file_upload_page]

        # Create & assign stepper children
        stepper_children = []
        for i in range(0, NUM_OF_PAGES):
            page_number = ui.HTML(value=str(i + 1))
            separator = ui.HTML("<hr width=48px/>")
            page_title = ui.HTML(PAGE_TITLES[i])

            page_number.add_class("c-stepper__number")

            # Available modifiers are current, active, inactive
            page_number.add_class("c-stepper__number--current" if i == 0 else "c-stepper__number--inactive")
            # Available modifiers are active, inactive
            page_title.add_class("c-stepper__title--active" if i == 0 else "c-stepper__title--inactive")
            separator.add_class("c-stepper__separator--inactive")

            is_last_page = i == NUM_OF_PAGES - 1
            stepper_children += [page_number, page_title] if is_last_page else [page_number, page_title, separator]

        self.stepper.children = stepper_children

        return app_container

    def _build_file_upload_page(self) -> ui.Box:
        INSTRUCTION = '<h3 style="margin: 0px;">Upload file to be processed</h3>'
        SUB_INSTRUCTION = '<span style="font-size: 15px; line-height: 20px; margin: 0px; color: var(--grey);">File should be in CSV format</span>'
        UPLOADED_FILE = '<div style="width: 125px; line-height: 36px;">Uploaded file</div>'
        SAMPLE_FILE = '<div style="width: 125px; line-height: 36px;">Sample file</div>'
        NO_FILES_UPLOADED = '<div \
            style="width: 365px; line-height: 36px; border-radius: 4px; padding: 0px 16px; background: var(--light-grey); color: white;">\
            No files uploaded\
        </div>'

        # Create file upload area
        upload_area_bg = ui.Box(
            [
                ui.HTML('<img src="upload_file.svg" width="80px" height="800px"/>'),
                ui.HTML("<div class=c-text-grey>Browse files from your computer</div>"),
            ]
        )
        upload_area_bg.add_class("c-upload-area__background")
        upload_area_overlay = ui.FileUpload()
        upload_area_overlay._dom_classes = ["c-upload-area__overlay-button"]
        upload_area = ui.Box([upload_area_bg, upload_area_overlay], layout=ui.Layout(margin="28px 0px"))
        upload_area._dom_classes = ["c-upload-area"]

        # Create snackbar to show uploaded file
        uploaded_file_title = ui.HTML("Test.csv")
        uploaded_file_title.add_class("c-snackbar__text")
        x_button = ui.Button(icon="times")
        x_button.add_class("c-icon-button")
        self.uploaded_file_snackbar = ui.Box(
            [
                uploaded_file_title,
                x_button,
            ],
        )
        self.uploaded_file_snackbar.add_class("c-snackbar")

        # Buttons
        download_button = ui.Button(description="Download", icon="download", button_style="info")
        download_button.on_click(lambda x: print("clicked download"))
        self.next_button = ui.Button(
            description="Next", disabled=True, layout=ui.Layout(align_self="flex-end", justify_self="flex-end")
        )

        return ui.VBox(
            [
                ui.VBox(
                    [
                        ui.VBox(
                            layout=ui.Layout(width="500px"),
                            children=[
                                ui.HTML(INSTRUCTION),
                                ui.HTML(SUB_INSTRUCTION),
                            ],
                        ),
                        upload_area,
                        ui.HBox(
                            [
                                ui.HTML(UPLOADED_FILE),
                                self.uploaded_file_snackbar,
                                # ui.HTML(NO_FILES_UPLOADED),
                            ],
                            layout=ui.Layout(width="500px", margin="0px 0px 4px 0px"),
                        ),
                        ui.HBox(
                            [ui.HTML(SAMPLE_FILE), download_button],
                            layout=ui.Layout(width="500px"),
                        ),
                    ],
                    layout=ui.Layout(flex="1", justify_content="center"),
                ),
                ui.VBox(
                    [
                        self.next_button,
                    ],
                    layout=ui.Layout(align_self="flex-end"),
                ),
            ],
            layout=ui.Layout(flex="1", width="100%", align_items="center", justify_content="center"),
        )

    def _build_data_specification_page(self) -> ui.Box:
        return ui.Box()

    def _build_integrity_checking_page(self) -> ui.Box:
        return ui.Box()

    def _build_plausibility_checking_page(self) -> ui.Box:
        return ui.Box()
