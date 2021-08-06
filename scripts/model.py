from __future__ import annotations  # Delay the evaluation of undefined types
from copy import copy
import csv
from datetime import date, datetime
import os
from pathlib import Path
import shutil
from typing import Any, Callable, Optional, Dict, Union, List, overload

import numpy as np
import pandas as pd
from pandas.core.frame import DataFrame
from pandas.core.groupby.generic import DataFrameGroupBy

from .utils import ApplicationMode, Delimiter
from .utils import JSAppModel
from .utils import UserPage
from .utils import VisualizationTab
from .domain import (
    InputDataEntity,
    InputDataDiagnosis,
    OutputDataEntity,
    DataRuleRepository,
    BadLabelInfo,
    UnknownLabelInfo,
)


def check_administrator_privilege() -> bool:
    """Return whether or not user can enter the admin mode"""
    username = os.popen("id -un").read().strip("\n")
    return username in ["raziq", "raziqraif", "lanzhao", "rcampbel"]

def get_user_globalecon_project_dirnames() -> list[str]:
    "Return the list of AgMIP projects that the current user is in"
    groups = os.popen("groups").read().strip("\n").split(" ")
    project_groups = [group for group in groups if "pr-agmipglobalecon" in group]
    project_dirnames = [p_group[len("pr-") :] for p_group in project_groups]
    if len(project_dirnames) == 0:
        # NOTE: This is just to make developing on local environment easier
        project_dirnames = ["agmipglobaleconagclim50iv"]
    return project_dirnames

def get_submitted_files_info() -> list[list[str]]:
    """Return a list of submitted files' info"""
    

class Model:
    WORKINGDIR_PATH = Path(__name__).parent.parent / "workingdir"  # <PROJECT_DIR>/workingdir
    UPLOADDIR_PATH = WORKINGDIR_PATH / "uploads"
    DOWNLOADDIR_PATH = WORKINGDIR_PATH / "downloads"
    SHAREDDIR_PATH = Path("/srv/irods/")

    def __init__(self):
        # Import MVC classes here to prevent circular import problem
        from .controller import Controller
        from .view import View

        # MVC attributes
        self.view: View
        self.controller: Controller
        # Base app states 
        self.javascript_model = JSAppModel()    # - object to facilitate information injection into the Javascript context
        self.application_mode = ApplicationMode.USER
        self.is_user_an_admin = check_administrator_privilege()
        self.current_user_page = UserPage.FILE_UPLOAD  # - current user mode page
        self.furthest_active_user_page = UserPage.FILE_UPLOAD  # - furthest/last active user mode page
        self.input_data_entity = InputDataEntity()  # - domain entity for input / uploaded data file
        self.input_data_diagnosis: InputDataDiagnosis = InputDataDiagnosis()  # - domain entity for input data diagnosis
        self.output_data_entity: OutputDataEntity = OutputDataEntity()  # - domain entity for output / processed data
        # File upload page's states
        self.INFOFILE_PATH = (  # - path of downloadeable info file
            self.WORKINGDIR_PATH / "AgMIP GlobalEcon Data Submission Info.zip"
        )
        self.USER_GLOBALECON_PROJECTS = [
            (dirname, dirname) for dirname in get_user_globalecon_project_dirnames()
        ]  # - GlobalEcon projects the user is a part of
        self.uploadedfile_name = ""
        self.associated_project_dirnames: list[str] = []  # - associated GlobalEcon projects for this submission
        # Data specification page's states
        # The states for this page have multiple dependencies, and changes to a state may trigger changes to
        # several other states. So, we only define 1 state as an instance attribute here, and will define the other
        # states as properties later. We also define the states as properties because changes made to them needs to be relayed to
        # to the domain model @ Aug 4, 2021
        self.VALID_MODEL_NAMES = DataRuleRepository.query_model_names()  # - valid model names
        # Integrity checking page's states
        # - result of row checks
        self.nrows_w_struct_issue = 0  # - number of rows with structural issues
        self.nrows_w_ignored_scenario = 0  # - number of rows with ignored scenario
        self.nrows_duplicates = 0  # - number of duplicate rows
        self.nrows_accepted = 0  # - number of rows that passed row checks
        # - paths to downloadable row files
        self.STRUCTISSUEFILE_PATH = self.DOWNLOADDIR_PATH / "Rows With Structural Issue.csv"
        self.DUPLICATESFILE_PATH = self.DOWNLOADDIR_PATH / "Duplicate Records.csv"
        self.IGNOREDSCENARIOFILE_PATH = self.DOWNLOADDIR_PATH / "Records With An Ignored Scenario.csv"
        self.ACCEPTEDFILE_PATH = self.DOWNLOADDIR_PATH / "Accepted Records.csv"
        # - result of label/field checks
        self.bad_labels_overview_tbl: list[list[str]] = []
        self.unknown_labels_overview_tbl: list[list[Union[str, bool]]] = []
        # - valid labels that can be used to fix an unknown field (based on its associated column)
        self.VALID_SCENARIOS = DataRuleRepository.query_scenarios()
        self.VALID_REGIONS = DataRuleRepository.query_regions()
        self.VALID_VARIABLES = DataRuleRepository.query_variables()
        self.VALID_ITEMS = DataRuleRepository.query_items()
        self.VALID_UNITS = DataRuleRepository.query_units()
        # Plausibility checking page's states
        self.outputfile_path = Path()  # - path to cleaned and processed file
        self.overridden_labels = 0
        self.active_visualization_tab = VisualizationTab.VALUE_TRENDS
        # - uploaded labels
        self.uploaded_scenarios: List[str] = []
        self.uploaded_regions: List[str] = []
        self.uploaded_items: List[str] = []
        self.uploaded_variables: List[str] = []
        self.uploaded_units: List[str] = []
        self.uploaded_years: List[str] = []
        # - states for value trends visualization
        self.valuetrends_scenario = ""
        self.valuetrends_region = ""
        self.valuetrends_variable = ""
        # TODO: Instead of exposing a grouped data frame to View, is it possible to create a plot in the domain layer
        # (under OutputDataEntity) and just display it in view? # Aug 5, 2021
        self.valuetrends_table: DataFrameGroupBy | None = None
        self.valuetrends_table_year_colname = ""
        self.valuetrends_table_value_colname = ""
        # - states for growth trends visualization
        self.growthtrends_scenario = ""
        self.growthtrends_region = ""
        self.growthtrends_variable = ""
        # TODO: Instead of exposing a grouped data frame to View, is it possible to create a plot in the domain layer
        # (under OutputDataEntity) and just display it in view? # Aug 5, 2021
        self.growthtrends_table: DataFrameGroupBy | None = None
        self.growthtrends_table_year_colname = ""
        self.growthtrends_table_value_colname = ""

    def intro(self, view: View, controller: Controller) -> None:  # type: ignore # noqa
        """Introduce MVC modules to each other"""
        self.view = view
        self.controller = controller

    # File upload page's methods

    def remove_uploaded_file(self) -> None:
        """Remove uploaded file from the upload directory"""
        assert len(self.uploadedfile_name) > 0
        file_path = self.UPLOADDIR_PATH / Path(self.uploadedfile_name)
        assert file_path.is_file()
        file_path.unlink()

    # Data specification page's methods

    def init_data_specification_page_states(self, file_name: str) -> Optional[str]:
        """
        Initialize the states in the data specification pages (only when it had just become active)
        Note that the page may become active / inactive multiple times.
        Return an error message if an error is encountered, else None
        @date 6/23/21
        """
        assert len(file_name) > 0
        # Re-initialize all states
        try:
            self.input_data_entity = InputDataEntity.create(self.UPLOADDIR_PATH / file_name)
        except Exception as e:
            return str(e)
        valid_delimiters = Delimiter.get_models()
        # Guess information about the input file
        self.input_data_entity.guess_delimiter(valid_delimiters)
        self.input_data_entity.guess_header_is_included()
        self.input_data_entity.guess_initial_lines_to_skip()
        self.input_data_entity.guess_model_name_n_column_assignments()

    def validate_data_specification_input(self) -> Optional[str]:
        """
        Validate the input in the data specification page
        Return a warning message if there's an invalid input, else None
        """
        if len(self.input_data_entity.model_name) == 0:
            return "Model name is empty"
        elif len(self.input_data_entity.delimiter) == 0:
            return "Delimiter is empty"
        elif int(self.input_data_entity.initial_lines_to_skip) < 0:
            return "Number of lines cannot be negative"
        elif len(self.assigned_scenario_column) == 0:
            return "Scenario column is empty"
        elif len(self.assigned_region_column) == 0:
            return "Region column is empty"
        elif len(self.assigned_variable_column) == 0:
            return "Variable column is empty"
        elif len(self.assigned_item_column) == 0:
            return "Item column is empty"
        elif len(self.assigned_unit_column) == 0:
            return "Unit column is empty"
        elif len(self.assigned_year_column) == 0:
            return "Year column is empty"
        elif len(self.assigned_value_column) == 0:
            return "Value column is empty"
        elif (  # Make sure there are no duplicate assignment, we should have a set of 7 columns
            len(
                set(
                    [
                        self.assigned_scenario_column,
                        self.assigned_region_column,
                        self.assigned_variable_column,
                        self.assigned_item_column,
                        self.assigned_unit_column,
                        self.assigned_year_column,
                        self.assigned_value_column,
                    ]
                )
            )
            < 7
        ):
            return "Output data has duplicate columns"
        return None

    # Integrity checking page's methods

    def init_integrity_checking_page_states(self) -> None:
        # Diagnose input data
        self.input_data_diagnosis = InputDataDiagnosis.create(self.input_data_entity)
        # Map diagnosis results to page states
        self.nrows_w_struct_issue = self.input_data_diagnosis.nrows_w_struct_issue
        self.nrows_w_ignored_scenario = self.input_data_diagnosis.nrows_w_ignored_scenario
        self.nrows_accepted = self.input_data_diagnosis.nrows_accepted
        self.nrows_duplicates = self.input_data_diagnosis.nrows_duplicate
        self.bad_labels_overview_tbl = [
            [label_info.label, label_info.associated_column, label_info.fix]
            for label_info in self.input_data_diagnosis.bad_labels
        ]
        self.unknown_labels_overview_tbl = [
            [
                label_info.label,
                label_info.associated_column,
                label_info.closest_match,
                label_info.fix,
                label_info.override,
            ]
            for label_info in self.input_data_diagnosis.unknown_labels
        ]
        MIN_LABEL_OVERVIEW_TABLE_NROWS = 3
        self.bad_labels_overview_tbl += [["-", "-", "-"] for _ in range(MIN_LABEL_OVERVIEW_TABLE_NROWS)]
        self.unknown_labels_overview_tbl += [["-", "-", "-", "", False] for _ in range(MIN_LABEL_OVERVIEW_TABLE_NROWS)]

    def validate_unknown_labels_table(self, unknown_labels_table: list[list[str | bool]]) -> str | None:
        """
        Validate unknown labels table
        Return an error message if there is any, or None
        """
        for row in unknown_labels_table:
            _, _, _, fix, override = row
            assert isinstance(fix, str)
            assert isinstance(override, bool)
            if override == True and fix.strip() != "":
                return "Unknown labels cannot be both fixed and overridden"

    # Plausibility checking page's methods

    def init_plausibility_checking_page_states(self, unknown_labels_table: list[list[str | bool]]) -> None:
        """
        Initialize plausibility checking states
        @date Jul 26 2021
        """
        # Pass unknown labels table back to input data diagnosis
        # NOTE: The table now contains the (fix or override) actions selected by the user
        # NOTE: Make sure to ignore dummy rows
        self.input_data_diagnosis.unknown_labels = [
            UnknownLabelInfo(
                label=str(row[0]),
                associated_column=str(row[1]),
                closest_match=str(row[2]),
                fix=str(row[3]),
                override=bool(row[4]),
            )
            for row in unknown_labels_table
        ]
        self.overridden_labels = len(
            [label_info for label_info in self.input_data_diagnosis.unknown_labels if label_info.override == True]
        )
        # Create output data based on information from input data and input data diagnosis
        self.output_data_entity = OutputDataEntity.create(self.input_data_entity, self.input_data_diagnosis)
        # Map attributes from output data entity to page states
        self.outputfile_path = self.output_data_entity.file_path
        self.uploaded_scenarios = ["", *self.output_data_entity.unique_scenarios]
        self.uploaded_regions = ["", *self.output_data_entity.unique_regions]
        self.uploaded_variables = ["", *self.output_data_entity.unique_variables]
        self.uploaded_items = ["", *self.output_data_entity.unique_items]
        # Reset active tab
        self.active_visualization_tab = VisualizationTab.VALUE_TRENDS
        # Set default values if they exist
        if "SSP2_NoMt_NoCC" in self.uploaded_scenarios:
            self.valuetrends_scenario = "SSP2_NoMt_NoCC"
            self.growthtrends_scenario = "SSP2_NoMt_NoCC"
        if "WLD" in self.uploaded_regions:
            self.valuetrends_region = "WLD"
            self.growthtrends_region = "WLD"
        if "PROD" in self.uploaded_variables:
            self.valuetrends_variable = "PROD"
            self.growthtrends_variable = "PROD"
        self.valuetrends_table = None
        self.growthtrends_table = None

    def update_valuetrends_visualization_states(self) -> None:
        """
        Initialize states for value trends visualization
        @date Aug 5, 2021
        """
        self.valuetrends_table_value_colname = self.output_data_entity.VALUE_COLNAME
        self.valuetrends_table_year_colname = self.output_data_entity.YEAR_COLNAME
        self.valuetrends_table = self.output_data_entity.get_value_trends_table(
            self.valuetrends_scenario, self.valuetrends_region, self.valuetrends_variable
        )

    def update_growthtrends_visualization_states(self) -> None:
        """
        Initialize states for value trends visualization
        @date Aug 5, 2021
        """
        self.growthtrends_table_value_colname = self.output_data_entity.VALUE_COLNAME
        self.growthtrends_table_year_colname = self.output_data_entity.YEAR_COLNAME
        self.growthtrends_table = self.output_data_entity.get_growth_trends_table(
            self.valuetrends_scenario, self.valuetrends_region, self.valuetrends_variable
        )

    def submit_processed_file(self) -> None:
        """Submit processed file to the correct directory"""
        for project_dirname in self.associated_project_dirnames:
            outputfile_dstpath = (
                self.SHAREDDIR_PATH / project_dirname / ".submissions" / ".pending" / self.outputfile_path.name
                if self.overridden_labels > 0
                else self.SHAREDDIR_PATH / project_dirname / ".submissions" / self.outputfile_path.name
            )
            shutil.copy(self.outputfile_path, outputfile_dstpath)
            # Submit a file detailing override request or create a new data cube
            if self.overridden_labels > 0:
                requestinfo_dstpath = outputfile_dstpath.parent / (outputfile_dstpath.stem + "_OverrideInfo.csv")
                with open(str(requestinfo_dstpath), "w+") as infofile:
                    for label_info in self.input_data_diagnosis.unknown_labels:
                        if label_info.override == True:
                            line = f"{label_info.label},{label_info.associated_column},{label_info.closest_match}\n"
                            infofile.write(line)
            else:
                submissiondir_path = outputfile_dstpath.parent
                submission_files_wildcard = str(submissiondir_path / "*.csv")
                # Print the content of all submission files, remove duplicates, and redirect the output to merged.csv
                os.system(f"cat {submission_files_wildcard} | uniq > merged.csv")

    # Data specification page's properties
    # NOTE: See the comment in contructor for the reasoning behind these properties.
    # NOTE: Most property getters below can removed if we allow View to read from the domain layer directly. The same
    # holds true for most property setters below if we allow Controller to write to the domain layer directly. However,
    # exposing the domain entity to View and Controller could create unwanted dependencies.
    # @date Aug 5, 2021

    # - properties for input format specification section

    @property
    def model_name(self) -> str:
        return self.input_data_entity.model_name

    @model_name.setter
    def model_name(self, value) -> None:
        self.input_data_entity.model_name = value

    @property
    def header_is_included(self) -> bool:
        return self.input_data_entity.header_is_included

    @header_is_included.setter
    def header_is_included(self, value: bool) -> None:
        self.input_data_entity.header_is_included = value

    @property
    def delimiter(self) -> str:
        return self.input_data_entity.delimiter

    @delimiter.setter
    def delimiter(self, value: str) -> None:
        assert value in Delimiter.get_models() or value == ""
        self.input_data_entity.delimiter = value
        self.input_data_entity.guess_model_name_n_column_assignments()

    @property
    def lines_to_skip(self) -> int:
        return self.input_data_entity.initial_lines_to_skip

    @lines_to_skip.setter
    def lines_to_skip(self, value: int) -> None:
        assert value >= 0
        self.input_data_entity.initial_lines_to_skip = value
        self.input_data_entity.guess_model_name_n_column_assignments()

    @property
    def scenarios_to_ignore_str(self) -> str:
        return "".join(self.input_data_entity.scenarios_to_ignore)

    @scenarios_to_ignore_str.setter
    def scenarios_to_ignore_str(self, value) -> None:
        value = value.strip()
        scenarios = value.split(",") if value != "" else []
        scenarios = [scenario.strip() for scenario in scenarios]
        self.input_data_entity.scenarios_to_ignore = scenarios

    # - properties for column assignment section

    @property
    def column_assignment_options(self) -> list[str]:
        input_header = list(self.input_data_preview_content[0])  # The header / first row of the input data preview
        return [] if "" in input_header else input_header  # Assumption: Empty string is only present when the header
        # row is empty

    @property
    def assigned_scenario_column(self) -> str:
        return ("", *self.column_assignment_options)[self.input_data_entity.scenario_colnum]

    @assigned_scenario_column.setter
    def assigned_scenario_column(self, value: str):
        self.input_data_entity.scenario_colnum = ([""] + self.column_assignment_options).index(value)

    @property
    def assigned_region_column(self) -> str:
        return ([""] + self.column_assignment_options)[self.input_data_entity.region_colnum]

    @assigned_region_column.setter
    def assigned_region_column(self, value: str):
        self.input_data_entity.region_colnum = ([""] + self.column_assignment_options).index(value)

    @property
    def assigned_variable_column(self) -> str:
        return ([""] + self.column_assignment_options)[self.input_data_entity.variable_colnum]

    @assigned_variable_column.setter
    def assigned_variable_column(self, value: str):
        self.input_data_entity.variable_colnum = ([""] + self.column_assignment_options).index(value)

    @property
    def assigned_item_column(self) -> str:
        return ([""] + self.column_assignment_options)[self.input_data_entity.item_colnum]

    @assigned_item_column.setter
    def assigned_item_column(self, value: str):
        self.input_data_entity.item_colnum = ([""] + self.column_assignment_options).index(value)

    @property
    def assigned_unit_column(self) -> str:
        return ([""] + self.column_assignment_options)[self.input_data_entity.unit_colnum]

    @assigned_unit_column.setter
    def assigned_unit_column(self, value: str) -> None:
        self.input_data_entity.unit_colnum = ([""] + self.column_assignment_options).index(value)

    @property
    def assigned_year_column(self) -> str:
        return ([""] + self.column_assignment_options)[self.input_data_entity.year_colnum]

    @assigned_year_column.setter
    def assigned_year_column(self, value: str) -> None:
        self.input_data_entity.year_colnum = ([""] + self.column_assignment_options).index(value)

    @property
    def assigned_value_column(self) -> str:
        return ([""] + self.column_assignment_options)[self.input_data_entity.value_colnum]

    @assigned_value_column.setter
    def assigned_value_column(self, value: str) -> None:
        self.input_data_entity.value_colnum = ([""] + self.column_assignment_options).index(value)

    # - properties for data preview sections

    @property
    def input_data_preview_content(self) -> np.ndarray:
        """Return preview table content in an ndarray"""
        # Get constants
        NROWS = 3
        DEFAULT_CONTENT = np.array(["" for _ in range(3)]).reshape((NROWS, 1))
        preview_table = self.input_data_entity.sample_parsed_input_data[:NROWS]
        # Make sure we have enough number of rows
        if len(preview_table) == 0:
            return DEFAULT_CONTENT
        elif len(preview_table) < 3:
            ncolumns = len(preview_table[0])
            empty_row = ["" for _ in range(ncolumns)]
            preview_table = (preview_table + [empty_row, empty_row])[:NROWS]  # add empty rows and trim excess rows
        # Prepare header row
        if self.input_data_entity.header_is_included:
            # Prepend header cells with a), b), c), d) ...
            A_ASCII = 97
            preview_table[0] = [
                chr(A_ASCII + col_idx) + ")  " + preview_table[0][col_idx] for col_idx in range(len(preview_table[0]))
            ]
        else:
            # Create header row
            ncolumns = len(preview_table[0])
            header = ["Column " + str(i + 1) for i in range(ncolumns)]
            preview_table = [header] + preview_table[: NROWS - 1]
        return np.array(preview_table)

    @property
    def output_data_preview_content(self) -> np.ndarray:
        """
        Return preview table content in an ndarray
        The content is built on top of the input data preview content
        @date 6/23/21
        """
        NROWS = 3
        # Lambda func. to return column content, given the title and column number assignment
        assert self.input_data_preview_content.shape[0] >= NROWS
        get_column_content: Callable[[str, int], list[str]] = (
            lambda title, assigned_colnum: [title] + ["" for _ in range(NROWS - 1)]
            if assigned_colnum == 0
            else [title] + [self.input_data_preview_content[row][assigned_colnum - 1] for row in range(1, NROWS)]
        )
        # Get the content of all columns
        model_col = ["Model", self.input_data_entity.model_name, self.input_data_entity.model_name]
        scenario_col = get_column_content("Scenario", self.input_data_entity.scenario_colnum)
        region_col = get_column_content("Region", self.input_data_entity.region_colnum)
        variable_col = get_column_content("Variable", self.input_data_entity.variable_colnum)
        item_col = get_column_content("Item", self.input_data_entity.item_colnum)
        unit_col = get_column_content("Unit", self.input_data_entity.unit_colnum)
        year_col = get_column_content("Year", self.input_data_entity.year_colnum)
        value_col = get_column_content("Value", self.input_data_entity.value_colnum)
        return np.array(
            [model_col, scenario_col, region_col, variable_col, item_col, unit_col, year_col, value_col]
        ).transpose()
