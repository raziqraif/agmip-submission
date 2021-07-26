from __future__ import annotations  # Delay the evaluation of undefined types
from copy import copy
import csv
from datetime import date, datetime
import os
from pathlib import Path
from typing import Any, Callable, Optional, Dict, Union

import numpy as np
import pandas as pd
from pandas.core.frame import DataFrame
from pandas.core.groupby.generic import DataFrameGroupBy

from .namespaces import Page
from .namespaces import VisualizationTab
from .view import Delimiter
from .dataaccess import RuleGateway
from .business import DataSpecification, DataCleaningService


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


class Model:
    WORKINGDIR_PATH = Path(__name__).parent.parent / "workingdir"  # <PROJECT_DIR>/workingdir
    UPLOADDIR_PATH = WORKINGDIR_PATH / "uploads"
    DOWNLOADDIR_PATH = WORKINGDIR_PATH / "downloads"
    SUBMISSIONDIR_PATH = Path("/srv/irods/agmipglobalecondata/.submissions")

    def __init__(self):
        # Import MVC classes here to prevent circular import problem
        from .controller import Controller
        from .view import View

        # MVC attributes
        self.view: View
        self.controller: Controller
        # App states
        self.javascript_model = JSAppModel()
        self.current_page = Page.FILE_UPLOAD
        self.furthest_active_page = Page.FILE_UPLOAD  # furthest/last active page
        # States for file upload page
        self.uploadedfile_name = ""  # Tracks uploaded file's name (should be empty when the file was removed)
        self.samplefile_path = self.DOWNLOADDIR_PATH / "SampleData.csv"
        # States for data specification page
        self.model_names = RuleGateway.query_model_names()
        self.data_specification = DataSpecification()
        # States for integrity checking page
        self.datacleaner: DataCleaningService | None = None
        # - simple statistics for row/record checks
        self.nrows_w_struct_issue = 0
        self.nrows_w_ignored_scenario = 0
        self.nrows_duplicates = 0
        self.nrows_accepted = 0
        # - paths to downloadable files
        self.structissuefile_path = self.DOWNLOADDIR_PATH / "RowsWithStructuralIssue.csv"
        self.duplicatesfile_path = self.DOWNLOADDIR_PATH / "DuplicateRecords.csv"
        self.ignoredscenariofile_path = self.DOWNLOADDIR_PATH / "RecordsWithIgnoredScenario.csv"
        self.acceptedfile_path = self.DOWNLOADDIR_PATH / "AcceptedRecords.csv"
        self.outputfile_path = self.DOWNLOADDIR_PATH / "OutputTable.csv"
        # - tables to summarize "field checks"
        self.bad_labels_table: list[list[str]] = []
        self.unknown_labels_table: list[list[Union[str, bool]]] = []
        # - valid labels for fixing
        self.valid_scenarios = RuleGateway.query_scenarios()
        self.valid_regions = RuleGateway.query_regions()
        self.valid_variables = RuleGateway.query_variables()
        self.valid_items = RuleGateway.query_items()
        self.valid_units = RuleGateway.query_units()
        # States for plausibility checking page
        self.active_visualization_tab = VisualizationTab.VALUE_TRENDS
        self.valuetrends_year_colname = ""
        self.valuetrends_value_colname = ""
        self.growthtrends_year_colname = ""
        self.growthtrends_growthvalue_colname = ""
        self.valuetrends_vis_groupedtable: DataFrameGroupBy | None = None
        self.growthtrends_vis_groupedtable: DataFrameGroupBy | None = None
        # - uploaded labels
        self.uploaded_scenarios = []
        self.uploaded_regions = []
        self.uploaded_items = []
        self.uploaded_variables = []
        self.uploaded_units = []
        self.uploaded_years = []
        # - selections for value trends visualization
        self.valuetrends_scenario = ""
        self.valuetrends_region = ""
        self.valuetrends_variable = ""
        # - selections for growth trends visualization
        self.growthtrends_scenario = ""
        self.growthtrends_region = ""
        self.growthtrends_variable = ""

    def intro(self, view: View, controller: Controller) -> None:  # type: ignore # noqa
        """Introduce MVC modules to each other"""
        self.view = view
        self.controller = controller

    def remove_file(self, file_name: str) -> None:
        """Remove uploaded file from the upload directory"""
        assert len(file_name) > 0
        file_path = self.UPLOADDIR_PATH / Path(file_name)
        assert file_path.is_file()
        file_path.unlink()

    @property
    def model_name(self) -> str:
        return self.data_specification.model_name

    @model_name.setter
    def model_name(self, value) -> None:
        self.data_specification.model_name = value

    @property
    def header_is_included(self) -> bool:
        return self.data_specification.header_is_included

    @header_is_included.setter
    def header_is_included(self, value: bool) -> None:
        self.data_specification.header_is_included = value

    @property
    def delimiter(self) -> str:
        return self.data_specification.delimiter

    @delimiter.setter
    def delimiter(self, value: str) -> None:
        assert value in Delimiter.get_models() or value == ""
        self.data_specification.delimiter = value
        self.data_specification.guess_model_name_n_column_assignments()

    @property
    def lines_to_skip(self) -> int:
        return self.data_specification.initial_lines_to_skip

    @lines_to_skip.setter
    def lines_to_skip(self, value: int) -> None:
        assert value >= 0
        old_value = self.data_specification.initial_lines_to_skip
        self.data_specification.initial_lines_to_skip = value
        file_nrows = self.data_specification.file_nrows
        if (old_value > file_nrows) and (value < file_nrows):
            self.data_specification.guess_model_name_n_column_assignments()

    @property
    def scenarios_to_ignore_str(self) -> str:
        return "".join(self.data_specification.scenarios_to_ignore)

    @scenarios_to_ignore_str.setter
    def scenarios_to_ignore_str(self, value) -> None:
        value = value.strip()
        scenarios = value.split(",") if value != "" else []
        scenarios = [scenario.strip() for scenario in scenarios]
        self.data_specification.scenarios_to_ignore = scenarios

    @property
    def column_assignment_options(self) -> list[str]:
        input_header = list(self.input_data_preview_content[0])  # The header / first row of the input data preview
        return [] if "" in input_header else input_header  # Assumption: Empty string is only present when the header
        # row is empty

    @property
    def assigned_scenario_column(self) -> str:
        return ("", *self.column_assignment_options)[self.data_specification.scenario_colnum]

    @assigned_scenario_column.setter
    def assigned_scenario_column(self, value: str):
        self.data_specification.scenario_colnum = ([""] + self.column_assignment_options).index(value)

    @property
    def assigned_region_column(self) -> str:
        return ([""] + self.column_assignment_options)[self.data_specification.region_colnum]

    @assigned_region_column.setter
    def assigned_region_column(self, value: str):
        self.data_specification.region_colnum = ([""] + self.column_assignment_options).index(value)

    @property
    def assigned_variable_column(self) -> str:
        return ([""] + self.column_assignment_options)[self.data_specification.variable_colnum]

    @assigned_variable_column.setter
    def assigned_variable_column(self, value: str):
        self.data_specification.variable_colnum = ([""] + self.column_assignment_options).index(value)

    @property
    def assigned_item_column(self) -> str:
        return ([""] + self.column_assignment_options)[self.data_specification.item_colnum]

    @assigned_item_column.setter
    def assigned_item_column(self, value: str):
        self.data_specification.item_colnum = ([""] + self.column_assignment_options).index(value)

    @property
    def assigned_unit_column(self) -> str:
        return ([""] + self.column_assignment_options)[self.data_specification.unit_colnum]

    @assigned_unit_column.setter
    def assigned_unit_column(self, value: str) -> None:
        self.data_specification.unit_colnum = ([""] + self.column_assignment_options).index(value)

    @property
    def assigned_year_column(self) -> str:
        return ([""] + self.column_assignment_options)[self.data_specification.year_colnum]

    @assigned_year_column.setter
    def assigned_year_column(self, value: str) -> None:
        self.data_specification.year_colnum = ([""] + self.column_assignment_options).index(value)

    @property
    def assigned_value_column(self) -> str:
        return ([""] + self.column_assignment_options)[self.data_specification.value_colnum]

    @assigned_value_column.setter
    def assigned_value_column(self, value: str) -> None:
        self.data_specification.value_colnum = ([""] + self.column_assignment_options).index(value)

    @property
    def input_data_preview_content(self) -> np.ndarray:
        """Return preview table content in an ndarray"""
        # Get constants
        NROWS = 3
        DEFAULT_CONTENT = np.array(["" for _ in range(3)]).reshape((NROWS, 1))
        # Process table content
        preview_table = self.data_specification.sample_processed_input_data[:NROWS]
        if len(preview_table) == 0:
            return DEFAULT_CONTENT
        elif len(preview_table) < 3:
            ncolumns = len(preview_table[0])
            empty_row = ["" for _ in range(ncolumns)]
            preview_table = (preview_table + [empty_row, empty_row])[:NROWS]  # add empty rows and trim excess rows
        if self.data_specification.header_is_included:
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
        model_col = ["Model", self.data_specification.model_name, self.data_specification.model_name]
        scenario_col = get_column_content("Scenario", self.data_specification.scenario_colnum)
        region_col = get_column_content("Region", self.data_specification.region_colnum)
        variable_col = get_column_content("Variable", self.data_specification.variable_colnum)
        item_col = get_column_content("Item", self.data_specification.item_colnum)
        unit_col = get_column_content("Unit", self.data_specification.unit_colnum)
        year_col = get_column_content("Year", self.data_specification.year_colnum)
        value_col = get_column_content("Value", self.data_specification.value_colnum)
        return np.array(
            [model_col, scenario_col, region_col, variable_col, item_col, unit_col, year_col, value_col]
        ).transpose()

    def validate_data_specification_input(self) -> Optional[str]:
        """Return a warning message if there's an invalid input, else None"""
        if len(self.data_specification.model_name) == 0:
            return "Model name is empty"
        elif len(self.data_specification.delimiter) == 0:
            return "Delimiter is empty"
        elif int(self.data_specification.initial_lines_to_skip) < 0:
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
        elif (
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
            < 7  # If there are no duplicate assignment, we should have a set of 7 columns
        ):
            return "Output data has duplicate columns"
        return None

    def init_data_specification_states(self, file_name: str) -> Optional[str]:
        """
        Do necessary steps when entering the data specification page (only when it had just become active)
        Note that the page may become active / inactive multiple times.
        Returns an error message if an error is encountered, else None
        @date 6/23/21
        """
        assert len(file_name) > 0
        # Reset all states
        self.data_specification = DataSpecification()
        self.data_specification.uploaded_filepath = self.UPLOADDIR_PATH / file_name
        error_message = self.data_specification.load_file()
        if error_message is not None:
            return error_message
        valid_delimiters = Delimiter.get_models()
        self.data_specification.guess_delimiter(valid_delimiters)
        self.data_specification.guess_header_is_included()
        self.data_specification.guess_initial_lines_to_skip()
        self.data_specification.guess_model_name_n_column_assignments()

    def init_integrity_checking_states(self, data_specification: DataSpecification) -> None:
        # Split raw csv rows
        self.datacleaner = DataCleaningService(data_specification)
        self.datacleaner.parse_data()
        self.nrows_w_struct_issue = self.datacleaner.nrows_w_struct_issue
        self.nrows_w_ignored_scenario = self.datacleaner.nrows_w_ignored_scenario
        self.nrows_accepted = self.datacleaner.nrows_accepted
        self.nrows_duplicates = self.datacleaner.nrows_duplicate
        self.bad_labels_table = copy(self.datacleaner.bad_labels_table)  # don't want to mutate the original table
        self.unknown_labels_table = copy(
            self.datacleaner.unknown_labels_table
        )  # don't want to mutate the original table
        BAD_LABELS_NROWS = 3
        UNKNOWN_LABELS_NROWS = 3
        if len(self.bad_labels_table) < BAD_LABELS_NROWS:
            self.bad_labels_table += [["-", "-", "-"] for _ in range(BAD_LABELS_NROWS)]
            self.bad_labels_table[:BAD_LABELS_NROWS]
        if len(self.unknown_labels_table) < UNKNOWN_LABELS_NROWS:
            self.unknown_labels_table += [["-", "-", "-", "", False] for _ in range(UNKNOWN_LABELS_NROWS)]
            self.unknown_labels_table[:UNKNOWN_LABELS_NROWS]
        self.outputfile_path = self.DOWNLOADDIR_PATH / (Path(self.uploadedfile_name).stem + datetime.now().strftime("_%b%d%Y_%H%M%S").upper() + ".csv")
    def validate_unknown_labels_table(self, unknown_labels_table: list[list[str | bool]]) -> str | None:
        """Validate unknown labels table"""
        for row in unknown_labels_table:
            _, _, _, fix, override = row
            assert isinstance(fix, str)
            assert isinstance(override, bool)
            if override == True and fix.strip() != "":
                return "Unknown labels cannot be both fixed and overridden"

    def init_plausibility_checking_states(self, unknown_labels_table: list[list[str | bool]]) -> None:
        """
        Initialize plausibility checking states
        @date Jul 26 2021
        """
        assert self.datacleaner is not None
        # Pass unknown label tables back to data cleaner
        # NOTE: The table now contains the (fix or override) actions selected by the user
        # NOTE: We need to make sure dummy rows are pruned before passing the table
        self.datacleaner.unknown_labels_table = [row for row in unknown_labels_table if row[0] != "-"]
        self.datacleaner.process_bad_and_unknown_labels()
        # Get a list of unique uploaded labels
        # NOTE: The lists are prepended with empty string,for ease-of-use (by the View object)
        # NOTE: Some of the columns in processed table may contain categorical data, which can't be sorted straight
        # away, so we need to pass them to np.assarray first  @date jul 26, 2021
        self.uploaded_scenarios = np.asarray(
            np.append(self.datacleaner.processed_table[self.datacleaner.scenario_colname].unique(), "")
        )
        self.uploaded_scenarios.sort()
        self.uploaded_regions = np.asarray(
            np.append(self.datacleaner.processed_table[self.datacleaner.region_colname].unique(), "")
        )
        self.uploaded_regions.sort()
        self.uploaded_variables = np.asarray(
            np.append(self.datacleaner.processed_table[self.datacleaner.variable_colname].unique(), "")
        )
        self.uploaded_variables.sort()
        self.uploaded_items = np.asarray(
            np.append(self.datacleaner.processed_table[self.datacleaner.item_colname].unique(), "")
        )
        self.uploaded_items.sort()
        self.uploaded_years = np.asarray(
            np.append(self.datacleaner.processed_table[self.datacleaner.year_colname].unique(), "")
        )
        self.uploaded_years.sort()
        self.uploaded_units = np.asarray(
            np.append(self.datacleaner.processed_table[self.datacleaner.unit_colname].unique(), "")
        )
        self.uploaded_units.sort()
        # Store processed table in a downloadable file
        self.datacleaner.processed_table.to_csv(self.outputfile_path, header=False, index=False)
        # Update default value
        if "SSP2_NoMt_NoCC" in self.uploaded_scenarios:
            self.valuetrends_scenario = "SSP2_NoMt_NoCC"
            self.growthtrends_scenario = "SSP2_NoMt_NoCC"
        if "WLD" in self.uploaded_regions:
            self.valuetrends_region = "WLD"
            self.growthtrends_region = "WLD"
        if "PROD" in self.uploaded_variables:
            self.valuetrends_variable = "PROD"
            self.growthtrends_variable = "PROD"

    def compute_valuetrends_vis_groupedtable(self) -> None:
        """Initialize grouped table for value trends visualization"""
        assert self.datacleaner is not None
        _table = self.datacleaner.processed_table
        _table = _table.loc[
            (_table[self.datacleaner.scenario_colname] == self.valuetrends_scenario)
            & (_table[self.datacleaner.region_colname] == self.valuetrends_region)
            & (_table[self.datacleaner.variable_colname] == self.valuetrends_variable)
        ].copy()
        if _table.shape[0] == 0:
            self.valuetrends_vis_groupedtable = None
            return
        # make sure that assignments to df's slice (which will not be reflected in the original df) does not raise any warning
        # pd.options.mode.chained_assignment = None
        _table[self.datacleaner.year_colname] = pd.to_numeric(_table[self.datacleaner.year_colname])
        _table[self.datacleaner.value_colname] = pd.to_numeric(_table[self.datacleaner.value_colname])
        # enable the warning back
        # pd.options.mode.chained_assignment = "warn"
        self.valuetrends_vis_groupedtable = _table.groupby(self.datacleaner.item_colname)
        self.valuetrends_year_colname = self.datacleaner.year_colname
        self.valuetrends_value_colname = self.datacleaner.value_colname

    def compute_growthtrends_vis_groupedtable(self) -> None:
        """Initialize grouped table for growth trends visualization"""
        assert self.datacleaner is not None
        _table = self.datacleaner.processed_table
        _table = _table.loc[
            (_table[self.datacleaner.scenario_colname] == self.growthtrends_scenario)
            & (_table[self.datacleaner.region_colname] == self.growthtrends_region)
            & (_table[self.datacleaner.variable_colname] == self.growthtrends_variable)
        ].copy()
        if _table.shape[0] == 0:
            self.growthtrends_vis_groupedtable = None
            return
        _table[self.datacleaner.year_colname] = pd.to_numeric(_table[self.datacleaner.year_colname])
        _table[self.datacleaner.value_colname] = pd.to_numeric(_table[self.datacleaner.value_colname])
        self.growthtrends_vis_groupedtable = _table.groupby(self.datacleaner.item_colname)
        self.growthtrends_year_colname = self.datacleaner.year_colname
        self.growthtrends_growthvalue_colname = self.datacleaner.value_colname
