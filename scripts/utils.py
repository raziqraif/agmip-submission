"""
Contains namespaces for various constants or utility methods
They are placed here for modularity reasons or to prevent circular imports between modules
@date Jun 30, 2021
"""
import os
from enum import Enum
import ipywidgets as ui
from typing import List


class VisualizationTab(Enum):
    """Enum for visualization tab's content"""

    VALUE_TRENDS = 0
    GROWTH_TRENDS = 1


class ApplicationMode:
    """Enum for application mode"""
    ADMIN = 0
    USER = 1


class UserPage:
    # TODO: Change this to enum
    """Namespace for the pages in this app"""

    FILE_UPLOAD = 1
    DATA_SPECIFICATION = 2
    INTEGRITY_CHECKING = 3
    PLAUSIBILITY_CHECKING = 4


class Delimiter:
    """ Namespace for supported CSV delimiters and relevant utilities """

    # TODO: ipywidgets dropdown supports dual representations for selection values, so this class is not needed 
    # @date Jul 27 2021
    
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
    def get_views(cls) -> List[str]:
        """Return all delimiter views"""
        delimiter_view_names = [name for name in cls.__dict__.keys() if cls._view_postfix in name]
        return [getattr(cls, name) for name in delimiter_view_names]

    @classmethod
    def get_models(cls) -> List[str]:
        """Return all delimiter models"""
        delimiter_model_names = [name for name in cls.__dict__.keys() if cls._model_postfix in name]
        return [getattr(cls, name) for name in delimiter_model_names]


class CSS:
    """Namespace for CSS classes declared in style.html and used inside Python"""

    APP = "rc-app-container"
    ASSOCIATED_PROJECT_SELECT = "rc-associated-project-select"
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
    ICON_BUTTON_MOD__RESTART_SUBMISSION = "rc-icon-button-mod--restart-submission"
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
    def get_cursor_mod_classes(cls) -> List[str]:
        name_prefix = "CURSOR_MOD__"
        names = [name for name in cls.__dict__.keys() if name_prefix in name]
        return [getattr(cls, name) for name in names]


class Notification:
    """Namespace for notification variants"""

    # Style variants
    ERROR = "error"
    INFO = "info"
    SUCCESS = "success"
    WARNING = "warning"
    _VARIANTS = [ERROR, INFO, SUCCESS, WARNING]

    # Content
    FILE_UPLOAD_SUCCESS = "File uploaded successfully"
    INVALID_FILE_FORMAT = "File format must be CSV"
    PLEASE_UPLOAD = "Please upload a CSV file first"
    FIELDS_WERE_PREPOPULATED = "Some fields have been prepopulated for you"

    # Icons
    WARNING_ICON = ui.HTML(
        value="""
        <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" fill="currentColor" class="bi bi-exclamation-triangle" viewBox="0 0 18 18"
            style="color: black; margin-right: 4px;" 
        >
            <path d="M7.938 2.016A.13.13 0 0 1 8.002 2a.13.13 0 0 1 .063.016.146.146 0 0 1 .054.057l6.857 11.667c.036.06.035.124.002.183a.163.163 0 0 1-.054.06.116.116 0 0 1-.066.017H1.146a.115.115 0 0 1-.066-.017.163.163 0 0 1-.054-.06.176.176 0 0 1 .002-.183L7.884 2.073a.147.147 0 0 1 .054-.057zm1.044-.45a1.13 1.13 0 0 0-1.96 0L.165 13.233c-.457.778.091 1.767.98 1.767h13.713c.889 0 1.438-.99.98-1.767L8.982 1.566z"/>
            <path d="M7.002 12a1 1 0 1 1 2 0 1 1 0 0 1-2 0zM7.1 5.995a.905.905 0 1 1 1.8 0l-.35 3.507a.552.552 0 0 1-1.1 0L7.1 5.995z"/>
        </svg>
        """
    )
    ERROR_ICON = ui.HTML(
        value="""
        <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" fill="currentColor" class="bi bi-exclamation-triangle" viewBox="0 0 18 18"
            style="color: white; margin-right: 4px;" 
        >
            <path d="M7.938 2.016A.13.13 0 0 1 8.002 2a.13.13 0 0 1 .063.016.146.146 0 0 1 .054.057l6.857 11.667c.036.06.035.124.002.183a.163.163 0 0 1-.054.06.116.116 0 0 1-.066.017H1.146a.115.115 0 0 1-.066-.017.163.163 0 0 1-.054-.06.176.176 0 0 1 .002-.183L7.884 2.073a.147.147 0 0 1 .054-.057zm1.044-.45a1.13 1.13 0 0 0-1.96 0L.165 13.233c-.457.778.091 1.767.98 1.767h13.713c.889 0 1.438-.99.98-1.767L8.982 1.566z"/>
            <path d="M7.002 12a1 1 0 1 1 2 0 1 1 0 0 1-2 0zM7.1 5.995a.905.905 0 1 1 1.8 0l-.35 3.507a.552.552 0 0 1-1.1 0L7.1 5.995z"/>
        </svg>
        """
    )
    INFO_ICON = ERROR_ICON
    SUCCESS_ICON = ui.HTML(
        value="""
        <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" fill="currentColor" class="bi bi-check-circle" viewBox="0 0 18 18"
            style="color: white; margin-right: 4px;" 
        >
            <path d="M8 15A7 7 0 1 1 8 1a7 7 0 0 1 0 14zm0 1A8 8 0 1 0 8 0a8 8 0 0 0 0 16z"/>
            <path d="M10.97 4.97a.235.235 0 0 0-.02.022L7.477 9.417 5.384 7.323a.75.75 0 0 0-1.06 1.06L6.97 11.03a.75.75 0 0 0 1.079-.02l3.992-4.99a.75.75 0 0 0-1.071-1.05z"/>
        </svg>
        """
    )


class JSAppModel:
    """Class to group attributes that needs to be passed to Javascript context"""

    def __init__(self):
        # Auth token of notebook server
        self.nbserver_auth_token: str = self._get_notebook_auth_token()
        # Model ID of the filename label in "UA" (upload area)
        self.ua_file_label_model_id: str = ""

    def serialize(self) -> str:
        """Serialize self into a format that can be embedded into the Javascript context"""
        return str(vars(self))

    def _get_notebook_auth_token(self) -> str:
        """Get auth token to interact with notebook server's API"""
        # Terminal command to print the urls of running servers.
        stream = os.popen("jupyter notebook list")
        output = stream.read()
        assert "http" in output
        # Assume our server is at the top of the output and extract its token
        # format of output -> "<title>\nhttp://<nbserver_baseurl>/?token=TOKEN :: ...\n"
        output = output.split("token=")[1]
        # Format of output is "TOKEN :: ..."
        token = output.split(" ")[0]
        return token
