from __future__ import annotations  # Delay the evaluation of undefined types
from copy import copy
import csv
import os
from pathlib import Path
from typing import Any, Callable, Optional, Dict, Union

import numpy as np
import pandas as pd
from pandas.core.frame import DataFrame

from .namespaces import Page
from .namespaces import VisualizationTab
from .view import Delimiter
from .labelgateway import LabelGateway
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
    WORKING_DIR: Path = Path(__name__).parent.parent / "workingdir"  # <PROJECT_DIR>/workingdir
    UPLOAD_DIR: Path = WORKING_DIR / "uploads"

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
        self.uploaded_filename = ""  # Tracks uploaded file's name (should be empty when the file was removed)
        # States for data specification page
        self.model_names = LabelGateway.query_model_names()
        self.data_specification = DataSpecification()
        # States for integrity checking page
        self.datacleaner: DataCleaningService | None = None
        self.nrows_w_struct_issue = 0
        self.nrows_w_ignored_scenario = 0
        self.nrows_duplicates = 0
        self.nrows_accepted = 0
        self.struct_issue_filepath = self.WORKING_DIR / "RowsWithStructuralIssue.csv"
        self.duplicates_filepath = self.WORKING_DIR / "DuplicateRecords.csv"
        self.ignored_scenario_filepath = self.WORKING_DIR / "RecordsWithIgnoredScenario.csv"
        self.accepted_filepath = self.WORKING_DIR / "AcceptedRecords.csv"
        self.output_filepath = self.WORKING_DIR / "OutputTable.csv"
        self.bad_labels_table: list[list[str]] = []
        self.unknown_labels_table: list[list[Union[str, bool]]] = []
        self.valid_scenarios = LabelGateway.query_scenarios()
        self.valid_regions = LabelGateway.query_regions()
        self.valid_variables = LabelGateway.query_variables()
        self.valid_items = LabelGateway.query_items()
        self.valid_units = LabelGateway.query_units()
        # States for plausibility checking page
        self.active_visualization_tab = VisualizationTab.VALUE_TRENDS
        self.uploaded_scenarios = []
        self.uploaded_regions = []
        self.uploaded_items = []
        self.uploaded_variables = []
        self.uploaded_units = []
        self.uploaded_years = []

    def intro(self, view: View, controller: Controller) -> None:  # type: ignore # noqa
        """Introduce MVC modules to each other"""
        self.view = view
        self.controller = controller

    def remove_file(self, file_name: str) -> None:
        """Remove uploaded file from the upload directory"""
        assert len(file_name) > 0
        file_path = self.UPLOAD_DIR / Path(file_name)
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
        self.data_specification.uploaded_filepath = self.UPLOAD_DIR / file_name
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
        """ 
        delimiter = data_specification.delimiter
        header_is_included = data_specification.header_is_included
        with open(str(data_specification.uploaded_filepath)) as csvfile:
            raw_csv = csvfile.readlines()
        scenarios_to_ignore = data_specification.scenarios_to_ignore
        scenario_colnum = data_specification.scenario_colnum
        region_colnum = data_specification.region_colnum
        item_colnum = data_specification.item_colnum
        variable_colnum = data_specification.variable_colnum
        unit_colnum = data_specification.unit_colnum
        year_colnum = data_specification.year_colnum
        value_colnum = data_specification.value_colnum
        assert delimiter != ""
        ROWS = [  # Each row contains the line number in the first column & header row is skipped
            [str(i + 1)] + raw_csv[i].split(delimiter) for i in range(int(header_is_included), len(raw_csv))
        ]
        MOST_FREQUENT_NCOLS = int(np.bincount([len(row) for row in ROWS]).argmax())
        # From ROWS, prune rows with field issues
        # - rows with mismatched number of fields
        # - rows with empty fields
        # - rows with a non-numeric value in a numeric field
        _rows_w_field_issues = []
        _rows_w_no_field_issues = []  # rows without field issues
        for row in ROWS:
            if len(row) != MOST_FREQUENT_NCOLS:
                row += ["Mismatched number of fields"]
                _rows_w_field_issues.append(row)
                continue
            elif "" in row:
                row += ["Contains empty fields"]
                _rows_w_field_issues.append(row)
                continue
            try:
                value = row[value_colnum]
                int(row[year_colnum])  # no need to set to 0-index due to the previously added line number column
                float(value)
            except:
                row += ["Non-numeric value in a numeric field"]
                _rows_w_field_issues.append(row)
                continue
            _rows_w_no_field_issues.append(row)
        # From rows with no field issues, prune rows containing an ignored scenario
        _rows_w_ignored_scenario = [
            row for row in _rows_w_no_field_issues if row[scenario_colnum] in scenarios_to_ignore
        ]
        _rows_w_no_ignored_scenario = [
            row for row in _rows_w_no_field_issues if row[scenario_colnum] not in scenarios_to_ignore
        ]
        # Initialize the integrity checking states
        _remaining_rows = pd.DataFrame(_rows_w_no_ignored_scenario)
        KEY_COLUMNS = _remaining_rows.columns.values.tolist()[1:]  # all columns except the line number column
        # -rows
        self.rows_w_field_issues = pd.DataFrame(_rows_w_field_issues)
        self.rows_w_ignored_scenario = pd.DataFrame(_rows_w_ignored_scenario)
        self.duplicate_rows = _remaining_rows[_remaining_rows.duplicated(subset=KEY_COLUMNS)]
        self.accepted_rows = _remaining_rows.drop_duplicates(subset=KEY_COLUMNS)
        # print("FIELD ISSUES:\n", self.rows_w_field_issues)
        # print("IGNORED:\n", self.rows_w_ignored_scenario)
        # print("DUPLICATES:\n", self.duplicate_rows)
        # print("ACCEPTED:\n", self.accepted_rows)
        # -uploaded labels
        self.uploaded_scenarios = self.accepted_rows.iloc[:, scenario_colnum].unique().tolist()
        self.uploaded_regions = self.accepted_rows.iloc[:, region_colnum].unique().tolist()
        self.uploaded_items = self.accepted_rows.iloc[:, item_colnum].unique().tolist()
        self.uploaded_variables = self.accepted_rows.iloc[:, variable_colnum].unique().tolist()
        self.uploaded_units = self.accepted_rows.iloc[:, unit_colnum].unique().tolist()
        self.uploaded_years = self.accepted_rows.iloc[:, year_colnum].unique().tolist()
        # -bad labels
        _bad_labels = []
        _unknown_labels = []
        for label in self.uploaded_scenarios:
            if label not in LabelGateway.valid_scenarios:
                _unknown_labels.append([label, "Scenario"])
            # matching_label = LabelGateway.query_matching_scenario(label)
            # if (matching_label != label) and (matching_label is not None):
            #     _bad_labels.append([label, "Scenario", matching_label])
            # elif (matching_label is None):
            #     _unknown_labels.append([label, "Scenario"])
        for label in self.uploaded_regions:
            if label not in LabelGateway.valid_regions:
                _unknown_labels.append([label, "Region"])
        for label in self.uploaded_items:
            if label not in LabelGateway.valid_items:
                _unknown_labels.append([label, "Item"])
        for label in self.uploaded_variables:
            if label not in LabelGateway.valid_variables:
                _unknown_labels.append([label, "Variable"])
        for label in self.uploaded_units:
            if label not in LabelGateway.valid_units:
                _unknown_labels.append([label, "Unit"])
            # matching_label = LabelGateway.query_matching_region(label)
            # fixed_label = LabelGateway.query_fix_from_region_fix_table(label)
            # if fixed_label is not None:
            #     _bad_labels.append([label, "Region", fixed_label])
            # elif (matching_label != label) and (matching_label is not None):
            #     _bad_labels.append([label, "Region", matching_label])
            # elif (matching_label is None):
            #     _unknown_labels.append([label, "Region"])
        self.bad_labels_overview = pd.DataFrame(_bad_labels)
        self.unknown_labels_overview = pd.DataFrame(_unknown_labels)
        print("Bad labels overview:\n", self.bad_labels_overview)
        print("")
        print("Unknown labels overview:\n", self.unknown_labels_overview)
        """

    def validate_unknown_labels_table(self, unknown_labels_table: list[list[str | bool]]) -> str | None:
        """Validate unknown labels table"""
        for row in unknown_labels_table:
            _, _, _, fix, override = row
            assert isinstance(fix, str)
            assert isinstance(override, bool)
            if override == True and fix.strip() != "":
                return "Unknown labels cannot be both fixed and overridden"

    def init_plausibility_checking_states(self) -> None:
        """Initialize plausibility checking states"""
        assert isinstance(self.datacleaner, DataCleaningService)
        # Pass unknown label tables back to data cleaner
        # Note: The table now contains the (fix or override) actions selected by the user
        # Note: We need to make sure dummy rows are pruned before passing the table
        self.datacleaner.unknown_labels_table = [row for row in self.unknown_labels_table if row[0] != "-"]
        self.datacleaner.process_bad_and_unknown_labels()
        # Get a list of unique uploaded labels
        # Note that some of the columns in processed table may contain categorical data, which can't be sorted straight
        # away
        self.uploaded_scenarios = np.asarray(
            self.datacleaner.processed_table[self.datacleaner.scenario_colname].unique()
        )
        self.uploaded_scenarios.sort()
        self.uploaded_regions = np.asarray(self.datacleaner.processed_table[self.datacleaner.region_colname].unique())
        self.uploaded_regions.sort()
        self.uploaded_variables = np.asarray(
            self.datacleaner.processed_table[self.datacleaner.variable_colname].unique()
        )
        self.uploaded_variables.sort()
        self.uploaded_items = np.asarray(self.datacleaner.processed_table[self.datacleaner.item_colname].unique())
        self.uploaded_items.sort()
        self.uploaded_years = np.asarray(self.datacleaner.processed_table[self.datacleaner.year_colname].unique())
        self.uploaded_years.sort()
        self.uploaded_units = np.asarray(self.datacleaner.processed_table[self.datacleaner.unit_colname].unique())
        self.uploaded_units.sort()
        # Store processed table in a downloadable file
        self.datacleaner.processed_table.to_csv(self.output_filepath, header=False, index=False)
