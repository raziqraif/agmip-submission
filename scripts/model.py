from __future__ import annotations  # Delay the evaluation of undefined types
import csv
import os
from pathlib import Path
from typing import Any, Callable, Optional

import numpy as np
import pandas as pd
from pandas.core.frame import DataFrame

from .view import Delimiter
from .namespaces import VisualizationTab


def get_notebook_auth_token() -> str:
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


class JSAppModel:
    """Class to group attributes that needs to be passed to Javascript context"""

    def __init__(self):
        # Auth token of notebook server
        self.nbserver_auth_token: str = get_notebook_auth_token()
        # Model ID of the filename label in "UA" (upload area)
        self.ua_file_label_model_id: str = ""

    def serialize(self) -> str:
        """Serialize self into a format that can be embedded into the Javascript context"""
        return str(vars(self))


class Step:
    """Namespace for the type of steps in this app"""

    INITIAL = 0
    FILE_UPLOAD = 1
    DATA_SPECIFICATION = 2
    INTEGRITY_CHECKING = 3
    PLAUSIBILITY_CHECKING = 4


class Model:
    WORKING_DIR: Path = Path(__name__).parent.parent / "workingdir"  # <PROJECT_DIR>/workingdir
    UPLOAD_DIR: Path = WORKING_DIR / "uploads"
    VALID_LABELS_SPREADSHEET: Path = WORKING_DIR / "valid_labels.xlsx"

    def __init__(self):
        # Import MVC classes here to prevent circular import problem
        from .controller import Controller
        from .view import View

        # MVC attributes
        self.view: View
        self.controller: Controller
        # States shared between pages
        self.javascript_model = JSAppModel()
        self.last_finished_step: int = Step.INITIAL
        # States for file upload page
        self.uploaded_filename: str = ""  # Tracks uploaded file's name (should be empty when the file was removed)
        # States for data specification page
        self._labels_spreadsheet: dict[str, pd.DataFrame] = pd.read_excel(
            str(self.VALID_LABELS_SPREADSHEET),
            engine="openpyxl",
            sheet_name=None,
            keep_default_na=False,
        )
        self.model_names: set[str] = set(
            self._labels_spreadsheet["Models"]["Model"]  # Get the pd dataframe, then the series
        )
        self.scenarios: set[str] = set(self._labels_spreadsheet["Scenarios"]["Scenario"])
        self.regions: set[str] = set(self._labels_spreadsheet["Regions"]["Region"])
        self.variables: set[str] = set(self._labels_spreadsheet["Variables"]["Variable"])
        self.items: set[str] = set(self._labels_spreadsheet["Items"]["Item"])
        self.units: set[str] = set(self._labels_spreadsheet["Units"]["Unit"])
        self.years: set[str] = set(self._labels_spreadsheet["Years"]["Year"])
        self.model_name: str = ""
        self._delimiter: str = ""
        self.header_is_included: bool = False
        self._lines_to_skip: int = 0
        self._scenarios_to_ignore_str: str = ""
        self._assigned_colnum_for_scenario: int = 0
        self._assigned_colnum_for_region: int = 0
        self._assigned_colnum_for_variable: int = 0
        self._assigned_colnum_for_item: int = 0
        self._assigned_colnum_for_unit: int = 0
        self._assigned_colnum_for_year: int = 0
        self._assigned_colnum_for_value: int = 0
        self.raw_csv_rows: list[str] = []  # "raw" -> each row is not separated by the csv delimiter yet
        self._sample_processed_csv_rows_memo: Optional[list[list[str]]] = None
        # States for integrity checking page
        self.rows_w_field_issues: pd.DataFrame = pd.DataFrame()
        self.rows_w_ignored_scenario: pd.DataFrame = pd.DataFrame()
        self.duplicate_rows: pd.DataFrame = pd.DataFrame()
        self.accepted_rows: pd.DataFrame = pd.DataFrame()
        # States for plausibility checking page
        self.active_visualization_tab: VisualizationTab = VisualizationTab.VALUE_TRENDS
        self.uploaded_scenarios: list = []
        self.uploaded_regions: list = []
        self.uploaded_items: list = []
        self.uploaded_variables: list = []
        self.uploaded_units: list = []
        self.uploaded_years: list = []

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
    def delimiter(self) -> str:
        return self._delimiter

    @delimiter.setter
    def delimiter(self, value: str) -> None:
        assert value in Delimiter.get_models() or value == ""
        self._delimiter = value
        self._reset_column_assignments()
        self._sample_processed_csv_rows_memo = None
        self.guess_model_name_n_column_assignments()

    @property
    def lines_to_skip(self) -> int:
        return self._lines_to_skip

    @lines_to_skip.setter
    def lines_to_skip(self, value: int) -> None:
        assert value >= 0
        old_value = self._lines_to_skip
        self._lines_to_skip = value
        self._sample_processed_csv_rows_memo = None
        if value > len(self.raw_csv_rows):
            self._reset_column_assignments()
        if (old_value > len(self.raw_csv_rows)) and (value < len(self.raw_csv_rows)):
            self.guess_model_name_n_column_assignments()

    @property
    def scenarios_to_ignore_str(self) -> str:
        return self._scenarios_to_ignore_str

    @scenarios_to_ignore_str.setter
    def scenarios_to_ignore_str(self, value) -> None:
        self._scenarios_to_ignore_str = value.strip()
        self._sample_processed_csv_rows_memo = None

    def _reset_column_assignments(self) -> None:
        """Reset column assignments"""
        self._assigned_colnum_for_scenario = 0
        self._assigned_colnum_for_region = 0
        self._assigned_colnum_for_variable = 0
        self._assigned_colnum_for_item = 0
        self._assigned_colnum_for_unit = 0
        self._assigned_colnum_for_year = 0
        self._assigned_colnum_for_value = 0

    @property
    def column_assignment_options(self) -> list[str]:
        input_header = list(self.input_data_preview_content[0])  # The header / first row of the input data preview
        return [] if "" in input_header else input_header  # Assumption: Empty string is only present when the header
        # row is empty

    @property
    def assigned_scenario_column(self) -> str:
        return ("", *self.column_assignment_options)[self._assigned_colnum_for_scenario]

    @assigned_scenario_column.setter
    def assigned_scenario_column(self, value: str):
        self._assigned_colnum_for_scenario = ([""] + self.column_assignment_options).index(value)

    @property
    def assigned_region_column(self) -> str:
        return ([""] + self.column_assignment_options)[self._assigned_colnum_for_region]

    @assigned_region_column.setter
    def assigned_region_column(self, value: str):
        self._assigned_colnum_for_region = ([""] + self.column_assignment_options).index(value)

    @property
    def assigned_variable_column(self) -> str:
        return ([""] + self.column_assignment_options)[self._assigned_colnum_for_variable]

    @assigned_variable_column.setter
    def assigned_variable_column(self, value: str):
        self._assigned_colnum_for_variable = ([""] + self.column_assignment_options).index(value)

    @property
    def assigned_item_column(self) -> str:
        return ([""] + self.column_assignment_options)[self._assigned_colnum_for_item]

    @assigned_item_column.setter
    def assigned_item_column(self, value: str):
        self._assigned_colnum_for_item = ([""] + self.column_assignment_options).index(value)

    @property
    def assigned_unit_column(self) -> str:
        return ([""] + self.column_assignment_options)[self._assigned_colnum_for_unit]

    @assigned_unit_column.setter
    def assigned_unit_column(self, value: str) -> None:
        self._assigned_colnum_for_unit = ([""] + self.column_assignment_options).index(value)

    @property
    def assigned_year_column(self) -> str:
        return ([""] + self.column_assignment_options)[self._assigned_colnum_for_year]

    @assigned_year_column.setter
    def assigned_year_column(self, value: str) -> None:
        self._assigned_colnum_for_year = ([""] + self.column_assignment_options).index(value)

    @property
    def assigned_value_column(self) -> str:
        return ([""] + self.column_assignment_options)[self._assigned_colnum_for_value]

    @assigned_value_column.setter
    def assigned_value_column(self, value: str) -> None:
        self._assigned_colnum_for_value = ([""] + self.column_assignment_options).index(value)

    @property
    def _sample_processed_csv_rows(self) -> list[list[str]]:
        """
        Process a subset of raw CSV rows by using delimiter, scenarios to ignore, and number of lines to skip;
        and return the result. The result is meant to be used for preview content & column assignment guessing.

        The processing done is not exhaustive and only includes:
        - Skipping initial rows
        - Splitting rows based on the delimiter
        - Removing rows containing ignored scenarios
        - Guessing the correct number of columns and removing rows with mismatched number of columns

        NOTE: To reduce performance hit, we limit the number of rows processed in this method and memoize
        the result
        @date 6/25/21
        """
        if self._sample_processed_csv_rows_memo is not None:
            return self._sample_processed_csv_rows_memo
        assert self.lines_to_skip >= 0
        ORIGINAL_NROWS = len(self.raw_csv_rows)
        TARGET_NROWS_BEFORE_DETECTING_NCOLS = 5000
        rows = []
        for row_idx in range(self.lines_to_skip, ORIGINAL_NROWS):
            raw_row = self.raw_csv_rows[row_idx]
            if self._row_contains_ignored_scenario(raw_row):
                continue
            split_row = raw_row.split(self.delimiter) if len(self.delimiter) > 0 else [raw_row]
            rows.append(split_row)
            if len(rows) == TARGET_NROWS_BEFORE_DETECTING_NCOLS:
                break
        if len(rows) == 0:
            self._sample_processed_csv_rows_memo = rows
            return rows
        # Use the most frequent no. of columns as a proxy for the no. of columns of a 'clean' row
        # NOTE: If the number of dirty rows > number of clean rows, we will have incorrect result here
        # @date 6/23/21
        _ncolumns_bincount: np.ndarray = np.bincount([len(row) for row in rows])
        most_frequent_ncolumns = int(_ncolumns_bincount.argmax())  # type-casted to raise error for non-int values
        # Prune rows with mismatched columns
        rows = [row for row in rows if len(row) == most_frequent_ncolumns]
        self._sample_processed_csv_rows_memo = rows
        return rows

    def _row_contains_ignored_scenario(self, raw_row: str) -> bool:
        """Check if the passed row contains a scenario to be ignored"""
        scenarios_to_ignore = [scenario.strip() for scenario in self.scenarios_to_ignore_str.split(",")]
        scenarios_to_ignore = [scenario for scenario in scenarios_to_ignore if len(scenario) > 0]
        scenario_col_index = self._assigned_colnum_for_scenario - 1
        for scenario in scenarios_to_ignore:
            if len(self.delimiter) > 0:
                split_row = raw_row.split(self.delimiter) if len(self.delimiter) > 0 else [raw_row]
                assert (scenario_col_index == -1) or (scenario_col_index < len(split_row))
                scenario_search_space = split_row[scenario_col_index] if scenario_col_index >= 0 else split_row
            else:
                scenario_search_space = raw_row
            if scenario in scenario_search_space:
                return True
        return False

    @property
    def input_data_preview_content(self) -> np.ndarray:
        """Return preview table content in an ndarray"""
        # Get constants
        NROWS = 3
        DEFAULT_CONTENT = np.array(["" for _ in range(3)]).reshape((NROWS, 1))
        # Process table content
        preview_table = self._sample_processed_csv_rows[:NROWS]
        if len(preview_table) == 0:
            return DEFAULT_CONTENT
        elif len(preview_table) < 3:
            ncolumns = len(preview_table[0])
            empty_row = ["" for _ in range(ncolumns)]
            preview_table = (preview_table + [empty_row, empty_row])[:NROWS]  # add empty rows and trim excess rows
        if self.header_is_included:
            # Prepend header cells with a), b), c), d) ...
            preview_table[0] = [
                chr(97 + col_idx) + ")  " + preview_table[0][col_idx] for col_idx in range(len(preview_table[0]))
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
        model_col = ["Model", self.model_name, self.model_name]
        scenario_col = get_column_content("Scenario", self._assigned_colnum_for_scenario)
        region_col = get_column_content("Region", self._assigned_colnum_for_region)
        variable_col = get_column_content("Variable", self._assigned_colnum_for_variable)
        item_col = get_column_content("Item", self._assigned_colnum_for_item)
        unit_col = get_column_content("Unit", self._assigned_colnum_for_unit)
        year_col = get_column_content("Year", self._assigned_colnum_for_year)
        value_col = get_column_content("Value", self._assigned_colnum_for_value)
        return np.array(
            [model_col, scenario_col, region_col, variable_col, item_col, unit_col, year_col, value_col]
        ).transpose()

    def init_data_specification_states(self, file_name: str) -> Optional[str]:
        """
        Do necessary steps when entering the data specification page (only when it had just become active)
        Note that the page may become active / inactive multiple times.
        Returns an error message if an error is encountered, else None
        @date 6/23/21
        """
        assert len(file_name) > 0
        # Reset all states
        self._delimiter = ""
        self.model_name = ""
        self.header_is_included = False
        self._lines_to_skip = 0
        self._scenarios_to_ignore_str = ""
        self.raw_csv_rows = []
        self._sample_processed_csv_rows_memo = None
        self._reset_column_assignments()
        # Read file content and sniff the CSV format
        file_path = self.UPLOAD_DIR / Path(file_name)
        assert file_path.is_file()
        try:  # Try to read file content
            with open(str(file_path)) as csvfile:
                self.raw_csv_rows = csvfile.readlines()
        except:
            return "Errror when opening file"
        self.guess_delimiter()
        self.guess_header_is_included()
        self.guess_lines_to_skip()
        self.guess_model_name_n_column_assignments()
        return None

    def guess_delimiter(self) -> bool:
        """Guess if a header row is included in the the CSV data and mutate the appropriate state
        Return True if the guess was successful, else False
        """
        # NOTE: number of initial lines to skip can be used to optimize the guess, but it's not used here to avoid
        # circular dependency when guessing - @date 6/23/21
        sample_data = "\n".join(self.raw_csv_rows[:1000])  # use X rows as sample data
        delimiters = "".join(Delimiter.get_models())
        format_sniffer = csv.Sniffer()
        try:
            csv_dialect = format_sniffer.sniff(sample_data, delimiters=delimiters)
        except csv.Error:  # Could be due to insufficient sample size, etc
            return False
        self._delimiter = csv_dialect.delimiter
        return True

    def guess_header_is_included(self) -> bool:
        """Guess if a header row is included in the the CSV data and mutate the appropriate state
        Return True if the guess was successful, else False
        """
        # NOTE: number of initial lines to skip can be used to optimize the guess, but it's not used here to avoid
        # circular dependency when guessing - @date 6/23/21
        sample_data = "\n".join(self.raw_csv_rows[:1000])  # use X rows as sample data
        format_sniffer = csv.Sniffer()
        try:
            self.header_is_included = format_sniffer.has_header(sample_data)
        except csv.Error:  # Could be due to insufficient sample size, etc
            return False
        return True

    def guess_lines_to_skip(self) -> bool:
        """
        Guess the initial number of lines to skip and mutate the appropriate state
        Return True if the guess was successful, else False
        """
        sample_raw_csv_rows = self.raw_csv_rows[:1000]
        rows = [row.split(self.delimiter) if len(self.delimiter) > 0 else [row] for row in sample_raw_csv_rows]
        if len(rows) == 0:
            return True
        # Use the most frequent no. of columns as a proxy for the no. of columns of a 'clean' row
        _ncolumns_bincount = np.bincount([len(row) for row in rows])
        most_frequent_ncolumns = int(_ncolumns_bincount.argmax())  # type-casted to raise error for non-int values
        self._lines_to_skip = 0
        for row in rows:
            if len(row) == most_frequent_ncolumns:
                break
            self.lines_to_skip += 1
        return True

    def guess_model_name_n_column_assignments(self) -> bool:
        """
        Guess the model name and column assignments, and mutate the appropariate states
        Return True if some guesses were successful, else False
        """
        sample_processed_csv_rows = self._sample_processed_csv_rows
        nrows = len(sample_processed_csv_rows)
        ncols = len(sample_processed_csv_rows[0]) if nrows > 0 else 0
        if nrows == 0 or ncols == 0:
            return False

        guessed_something = False
        for col_index in range(ncols):
            for row_index in range(nrows):
                cell_value = sample_processed_csv_rows[row_index][col_index]
                successful_guess_id = self._guess_model_name_n_column_assignments_util(cell_value, col_index)
                if successful_guess_id != -1:
                    guessed_something = True
                    break
        return guessed_something

    def _guess_model_name_n_column_assignments_util(self, cell_value: str, col_index: int) -> int:
        """
        Return -1 if no guesses were made, or a non-negative integer if a guess was made
        Each type of successful guess is associated with a unique non-negative integer
        """
        if cell_value in self.model_names:
            self.model_name = cell_value
            return 0
        elif cell_value in self.scenarios:
            self._assigned_colnum_for_scenario = col_index + 1
            return 1
        elif cell_value in self.regions:
            self._assigned_colnum_for_region = col_index + 1
            return 2
        elif cell_value in self.variables:
            self._assigned_colnum_for_variable = col_index + 1
            return 3
        elif cell_value in self.items:
            self._assigned_colnum_for_item = col_index + 1
            return 4
        elif cell_value in self.units:
            self._assigned_colnum_for_unit = col_index + 1
            return 5
        try:
            int(cell_value)  # Reminder: int(<float value in str repr>) will raise an error
            self._assigned_colnum_for_year = col_index + 1
            return 6
        except ValueError:
            pass
        try:
            float(cell_value)
            self._assigned_colnum_for_value = col_index + 1
            return 7
        except ValueError:
            pass
        return -1

    def init_integrity_checking_states(
        self,
        raw_csv: list[str],
        delimiter: str,
        header_is_included: bool,
        lines_to_skip: int,
        scenarios_to_ignore: set[str],
        model_name: str,
        scenario_colnum: int,
        region_colnum: int,
        variable_colnum: int,
        item_colnum: int,
        unit_colnum: int,
        year_colnum: int,
        value_colnum: int,
    ) -> None:
        # Split raw csv rows
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
                int(row[year_colnum])  # no need to set to 0-index due to the previously added line number column
                float(row[value_colnum])
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
        self.rows_w_field_issues = pd.DataFrame(_rows_w_field_issues)
        self.rows_w_ignored_scenario = pd.DataFrame(_rows_w_ignored_scenario)
        self.duplicate_rows = _remaining_rows[_remaining_rows.duplicated(subset=KEY_COLUMNS)]
        self.accepted_rows = _remaining_rows.drop_duplicates(subset=KEY_COLUMNS)
        self.uploaded_scenarios = self.accepted_rows.iloc[:, scenario_colnum].unique().tolist()
        self.uploaded_regions = self.accepted_rows.iloc[:, region_colnum].unique().tolist()
        self.uploaded_items = self.accepted_rows.iloc[:, item_colnum].unique().tolist()
        self.uploaded_variables = self.accepted_rows.iloc[:, variable_colnum].unique().tolist()
        self.uploaded_units = self.accepted_rows.iloc[:, unit_colnum].unique().tolist()
        self.uploaded_years = self.accepted_rows.iloc[:, year_colnum].unique().tolist()
