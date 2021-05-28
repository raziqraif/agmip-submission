from __future__ import annotations  # Delay the evaluation of undefined types

import ipywidgets as ui
from IPython.core.display import display


DARK_BLUE = "#1E3A8A"


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
        body_container.layout = ui.Layout(width="100%", height="100%", align_items="center", padding="36px 48px")
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
        return ui.Box()

    def _build_data_specification_page(self) -> ui.Box:
        return ui.Box()

    def _build_integrity_checking_page(self) -> ui.Box:
        return ui.Box()

    def _build_plausibility_checking_page(self) -> ui.Box:
        return ui.Box()
