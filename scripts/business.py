from __future__ import annotations
from copy import copy
from copy import deepcopy
import csv
from io import TextIOWrapper
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Optional, List, Dict, Set

from .labelgateway import LabelGateway


class DataSpecification:
    SAMPLE_NROWS = 1000  # rows
    DEFAULT_FILEPATH = Path()

    def __init__(self):
        self.__uploaded_filepath: Path = self.DEFAULT_FILEPATH
        self.model_name: str = ""
        self.__delimiter: str = ""
        self.header_is_included: bool = False
        self.__initial_lines_to_skip: int = 0
        self.scenarios_to_ignore: List[str] = []
        self.scenario_colnum: int = 0
        self.region_colnum: int = 0
        self.variable_colnum: int = 0
        self.item_colnum: int = 0
        self.unit_colnum: int = 0
        self.year_colnum: int = 0
        self.value_colnum: int = 0
        self.__file_nrows = 0
        self.__input_data_topmost_sample: list[str] = []
        self.__input_data_nonskipped_sample: list[str] = []
        self.__sample_processed_input_data_memo: Optional[list[list[str]]] = None

    @property
    def delimiter(self) -> str:
        return self.__delimiter

    @delimiter.setter
    def delimiter(self, value: str) -> None:
        self.__delimiter = value
        self.__sample_processed_input_data_memo = None

    @property
    def uploaded_filepath(self) -> Path:
        return self.__uploaded_filepath

    @uploaded_filepath.setter
    def uploaded_filepath(self, value: Path) -> None:
        if str(self.__uploaded_filepath) != str(self.DEFAULT_FILEPATH):
            raise Exception(
                "Uploaded file's path is not meant to be mutated multiple times. Please instantiate a new object for"
                " the new file path."
            )
        assert value.is_file()
        self.__uploaded_filepath = value

    @property
    def file_nrows(self) -> int:
        return self.__file_nrows

    @property
    def initial_lines_to_skip(self) -> int:
        return self.__initial_lines_to_skip

    @initial_lines_to_skip.setter
    def initial_lines_to_skip(self, value: int) -> None:
        assert value >= 0
        self.__initial_lines_to_skip = value
        self.__sample_processed_input_data_memo = None
        # Reset column assignments if all file content was skipped
        if value > self.file_nrows:
            self.scenario_colnum = 0
            self.region_colnum = 0
            self.variable_colnum = 0
            self.item_colnum = 0
            self.unit_colnum = 0
            self.year_colnum = 0
            self.value_colnum = 0
        # Recompute input data sample
        if value == 0:
            self.__input_data_nonskipped_sample = self.__input_data_topmost_sample
            return
        self.__input_data_nonskipped_sample = []
        try:
            with open(str(self.uploaded_filepath)) as csvfile:
                for line_index, line in enumerate(csvfile):
                    if (line_index >= self.initial_lines_to_skip) and (
                        line_index < self.SAMPLE_NROWS + self.initial_lines_to_skip
                    ):
                        self.__input_data_nonskipped_sample.append(line)
                    if line_index >= self.initial_lines_to_skip + self.SAMPLE_NROWS:
                        break
        except:
            return

    def load_file(self) -> Optional[str]:
        """Load file from the filepath"""
        file_path = self.uploaded_filepath
        assert file_path.is_file()
        self.__input_data_topmost_sample = []
        self.__input_data_nonskipped_sample = []
        try:
            with open(str(file_path)) as csvfile:
                for line_index, line in enumerate(csvfile):
                    if line_index <= self.SAMPLE_NROWS:
                        self.__input_data_topmost_sample.append(line)
                    if (line_index >= self.initial_lines_to_skip) and (
                        line_index < self.SAMPLE_NROWS + self.initial_lines_to_skip
                    ):
                        self.__input_data_nonskipped_sample.append(line)
                    self.__file_nrows += 1
        except:
            return "Error when opening file"
        return None

    def guess_delimiter(self, valid_delimiters: list[str]) -> bool:
        """Guess the delimiter from the sample input data and update the value
        Return True if the guess was successful, else False
        """
        sample = "\n".join(self.__input_data_topmost_sample)
        delimiters = "".join(valid_delimiters)
        format_sniffer = csv.Sniffer()
        try:
            csv_dialect = format_sniffer.sniff(sample, delimiters=delimiters)
        except csv.Error:  # Could be due to insufficient sample size, etc
            return False
        self.delimiter = csv_dialect.delimiter
        return True

    def guess_header_is_included(self) -> bool:
        """Guess if a header row is included in the sample input data and update the value
        Return True if the guess was successful, else False
        """
        sample = "\n".join(self.__input_data_topmost_sample)
        format_sniffer = csv.Sniffer()
        try:
            self.header_is_included = format_sniffer.has_header(sample)
        except csv.Error:  # Could be due to insufficient sample size, etc
            return False
        return True

    def guess_initial_lines_to_skip(self) -> bool:
        """Guess the initial number of lines to skip and update the value
        Return True if the guess was successful, else False
        """
        rows = [
            row.split(self.delimiter) if len(self.delimiter) > 0 else [row] for row in self.__input_data_topmost_sample
        ]
        if len(rows) == 0:
            return True
        # Use the most frequent no. of columns as a proxy for the no. of columns of a 'clean' row
        _ncolumns_bincount = np.bincount([len(row) for row in rows])
        most_frequent_ncolumns = int(_ncolumns_bincount.argmax())  # type-casted to raise error for non-int values
        # Skip initial lines with mimatched number of columns
        count = 0
        for row in rows:
            if len(row) == most_frequent_ncolumns:
                break
            count += 1
        # Assume the guess had failed if the guessed number is too much
        if count > self.SAMPLE_NROWS * 0.9:
            self.initial_lines_to_skip = 0
            return False
        self.initial_lines_to_skip = count
        return True

    def guess_model_name_n_column_assignments(self) -> bool:
        """
        Guess the model name and column assignments, and mutate the appropariate states
        Return True if some guesses were successful, else False
        """
        sample_processed_csv_rows = self.sample_processed_input_data
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
        if LabelGateway.query_label_in_model_names(cell_value):
            self.model_name = cell_value
            return 0
        elif LabelGateway.query_label_in_scenarios(cell_value):
            self.scenario_colnum = col_index + 1
            return 1
        elif LabelGateway.query_label_in_regions(cell_value):
            self.region_colnum = col_index + 1
            return 2
        elif LabelGateway.query_label_in_variables(cell_value):
            self.variable_colnum = col_index + 1
            return 3
        elif LabelGateway.query_label_in_items(cell_value):
            self.item_colnum = col_index + 1
            return 4
        elif LabelGateway.query_label_in_units(cell_value):
            self.unit_colnum = col_index + 1
            return 5
        try:
            int(cell_value)  # Reminder: int(<float value in str repr>) will raise an error
            self.year_colnum = col_index + 1
            return 6
        except ValueError:
            pass
        try:
            float(cell_value)
            self.value_colnum = col_index + 1
            return 7
        except ValueError:
            pass
        return -1

    @property
    def sample_processed_input_data(self) -> list[list[str]]:
        """
        Process a subset of the raw input data and return the result

        The processing done is not exhaustive and only includes:
        - Skipping initial rows
        - Splitting rows based on the delimiter
        - Guessing the correct number of columns and removing rows with mismatched number of columns

        NOTE: This property has many dependents, so it's value is memoized. Every time this property's
        dependencies (like delimiter) is updated, the memo must be reset.
        @date 7/6/21
        """
        if self.__sample_processed_input_data_memo is not None:
            return self.__sample_processed_input_data_memo
        rows = [
            row.split(self.delimiter) if self.delimiter != "" else [row] for row in self.__input_data_nonskipped_sample
        ]
        if len(rows) == 0:
            self.__sample_processed_input_data_memo = rows
            return rows
        # Use the most frequent no. of columns as a proxy for the no. of columns of a 'clean' row
        # NOTE: If the number of dirty rows > number of clean rows, we will have incorrect result here
        # @date 6/23/21
        _ncolumns_bincount: np.ndarray = np.bincount([len(row) for row in rows])
        most_frequent_ncolumns = int(_ncolumns_bincount.argmax())  # type-casted to raise error for non-int values
        # Prune rows with mismatched columns
        rows = [row for row in rows if len(row) == most_frequent_ncolumns]
        self.__sample_processed_input_data_memo = rows
        return rows


class DataCleaningService:
    """
    Service class for cleaning data
    @date July 5, 2021
    """

    WORKING_DIRPATH = Path(__name__).parent.parent / "workingdir"

    def __init__(self, data_specification: DataSpecification) -> None:
        self.data_specification = data_specification
        # Number of rows
        self.nrows_w_struct_issue = 0
        self.nrows_w_ignored_scenario = 0
        self.nrows_duplicate = 0
        self.nrows_accepted = 0
        # Destination files' path
        self.accepted_rows_dstpath = self.WORKING_DIRPATH / "AcceptedRecords.csv"
        self.duplicate_rows_dstpath = self.WORKING_DIRPATH / "DuplicateRecords.csv"
        self.rows_w_ignored_scenario_dstpath = self.WORKING_DIRPATH / "RecordsWithIgnoreScenario.csv"
        self.rows_w_struct_issue_dstpath = self.WORKING_DIRPATH / "RowsWithStructuralIssue.csv"
        # Label-related attributes
        self.fixed_labels_table = pd.DataFrame()
        self.unknown_labels_table = pd.DataFrame()
        self._uploaded_scenarios: Set[str] = set()
        self._uploaded_regions: Set[str] = set()
        self._uploaded_variables: Set[str] = set()
        self._uploaded_items: Set[str] = set()
        self._uploaded_years: Set[str] = set()
        self._uploaded_units: Set[str] = set()
        # Number of columns info
        self.__most_frequent_ncolumns = 0
        self.__largest_ncolumns = 0
        # Duplicate check helper
        self.__row_occurence_dict: Dict[str, int] = {}
        # Actions
        self.initialize_files()
        self._update_ncolumns_info()

    def parse_data(self) -> None:
        """Parse data and populate destination files and nrows attributes"""
        self.__init__(self.data_specification)  # Reset all attributes
        with open(str(self.data_specification.uploaded_filepath)) as datafile, open(
            str(self.rows_w_struct_issue_dstpath), "w+"
        ) as structissuefile, open(str(self.rows_w_ignored_scenario_dstpath), "w+") as ignoredscenfile, open(
            str(self.duplicate_rows_dstpath), "w+"
        ) as duplicatesfile, open(
            str(self.accepted_rows_dstpath), "w+"
        ) as acceptedfile:
            for line_idx, line in enumerate(datafile):
                rownum = line_idx + 1
                row = line.split(self.data_specification.delimiter)
                if self.parse_row_w_struct_issue(rownum, row, structissuefile):
                    continue
                if self.parse_row_w_ignored_scenario(rownum, row, ignoredscenfile):
                    continue
                if self.parse_duplicate_row(rownum, line, duplicatesfile):
                    continue
                acceptedfile.write(line)
                scenario_field = row[self.data_specification.scenario_colnum - 1]
                self._uploaded_scenarios.add(scenario_field)
                region_field = row[self.data_specification.region_colnum - 1]
                self._uploaded_regions.add(region_field)
                variable_field = row[self.data_specification.variable_colnum - 1]
                self._uploaded_variables.add(variable_field)
                item_field = row[self.data_specification.item_colnum - 1]
                self._uploaded_items.add(item_field)
                unit_field = row[self.data_specification.unit_colnum - 1]
                self._uploaded_items.add(unit_field)
                year_field = row[self.data_specification.year_colnum - 1]
                self._uploaded_items.add(year_field)
                value_field = row[self.data_specification.value_colnum - 1]
                # self.parse_value_field(value_field)
        # for label in self._uploaded_scenarios:
        #     self.parse_scenario_field(label)
        # for label in self._uploaded_regions:
        #     self.parse_region_field(label)
        # for label in self._uploaded_variables:
        #     self.parse_variable_field(label)
        # for label in self._uploaded_items:
        #     self.parse_item_field(label)
        # for label in self._uploaded_years:
        #     self.parse_year_field(label)
        # for label in self._uploaded_units:
        #     self.parse_unit_field(label)

    def parse_row_w_struct_issue(self, rownum: int, row: list[str], structissuefile: TextIOWrapper) -> bool:
        """
        Checks if a row has a structural issue and logs it into the file if it has.
        Returns the result of the structural check.

        Definition of structural issue for rows:
        1. A row has a structural issue if it has a wrong number of fields
        2. A row has a structural issue if it has a field with with structural issue

        Definition of structural issue for fields varies depending on the field type, and can be inferred from the
        implementation below.

        @date July 7, 2021
        """
        if len(row) != self.__most_frequent_ncolumns:
            log_text = self._format_row_w_struct_issue_for_logging(rownum, row, "Mismatched number of fields")
            structissuefile.write(log_text)
            return True
        if row[self.data_specification.scenario_colnum - 1] == "":
            log_text = self._format_row_w_struct_issue_for_logging(rownum, row, "Empty scenario field")
            structissuefile.write(log_text)
            return True
        if row[self.data_specification.region_colnum - 1] == "":
            log_text = self._format_row_w_struct_issue_for_logging(rownum, row, "Empty region field")
            structissuefile.write(log_text)
            return True
        if row[self.data_specification.variable_colnum - 1] == "":
            log_text = self._format_row_w_struct_issue_for_logging(rownum, row, "Empty variable field")
            structissuefile.write(log_text)
            return True
        if row[self.data_specification.item_colnum - 1] == "":
            log_text = self._format_row_w_struct_issue_for_logging(rownum, row, "Empty item field")
            structissuefile.write(log_text)
            return True
        if row[self.data_specification.unit_colnum - 1] == "":
            log_text = self._format_row_w_struct_issue_for_logging(rownum, row, "Empty unit field")
            structissuefile.write(log_text)
            return True
        year_field = row[self.data_specification.year_colnum]
        if year_field == "":
            log_text = self._format_row_w_struct_issue_for_logging(rownum, row, "Empty year field")
            structissuefile.write(log_text)
            return True
        try:
            int(year_field)
        except:
            log_text = self._format_row_w_struct_issue_for_logging(rownum, row, "Non-integer year field")
            structissuefile.write(log_text)
            return True
        value_field = row[self.data_specification.value_colnum - 1]
        try:
            value_fix = LabelGateway.query_fix_from_value_fix_table(value_field)
            value_fix = value_fix if value_fix is not None else value_field
            variable_field = row[self.data_specification.variable_colnum - 1]
            matching_variable = LabelGateway.query_matching_variable(variable_field)
            matching_variable = matching_variable if matching_variable is not None else variable_field
            min_value = LabelGateway.query_variable_min_value(matching_variable)
            max_value = LabelGateway.query_variable_max_value(matching_variable)
            if (min_value is not None) and (float(value_fix) < min_value):
                issue_text = "Value for variable {} is too small".format(matching_variable)
                log_text = self._format_row_w_struct_issue_for_logging(rownum, row, issue_text)
                structissuefile.write(log_text)
                return True
            if (max_value is not None) and (float(value_fix) > max_value):
                issue_text = "Value for variable {} is too large".format(matching_variable)
                log_text = self._format_row_w_struct_issue_for_logging(rownum, row, issue_text)
                structissuefile.write(log_text)
                return True
        except:
            log_text = self._format_row_w_struct_issue_for_logging(rownum, row, "Non-numeric value field")
            structissuefile.write(log_text)
            return True
        return False

    def parse_row_w_ignored_scenario(self, rownum, row, ignoredscenfile) -> bool:
        """
        Checks if a row contains an ignored scenario and logs it into the given file if it does.
        Returns the result of the check.
        """
        if row[self.data_specification.scenario_colnum - 1] in self.data_specification.scenarios_to_ignore:
            log_row = [rownum, *row]
            log_text = ",".join(log_row) + "\n"
            ignoredscenfile.write(log_text)
            return True
        return False

    def parse_duplicate_row(self, rownum: int, row: str, duplicatesfile: TextIOWrapper) -> bool:
        """
        Checks if a row is a duplicate and logs it into the duplicates file if it is.
        Returns the result of the check.
        """
        # NOTE: Finding duplicates with the help of an in-memory data structure might cause a problem if the dataset
        # is too large. If that proves to be the case, consider using solutions like SQL
        # @date 7/7/2021
        self.__row_occurence_dict[row] += 1
        occurence = self.__row_occurence_dict[row]
        if occurence > 1:
            log_text = "{},{},{}\n".format(rownum, row, occurence)
            duplicatesfile.write(log_text)
            return True
        return False

    def initialize_files(self):
        """Create/Recreate destination files"""
        # Deletes existing files, if any
        if self.rows_w_struct_issue_dstpath.exists():
            self.rows_w_struct_issue_dstpath.unlink()
        if self.rows_w_ignored_scenario_dstpath.exists():
            self.rows_w_ignored_scenario_dstpath.unlink()
        if self.duplicate_rows_dstpath.exists():
            self.duplicate_rows_dstpath.unlink()
        if self.accepted_rows_dstpath.exists():
            self.accepted_rows_dstpath.unlink()
        # Create files
        self.rows_w_struct_issue_dstpath.touch()
        self.rows_w_ignored_scenario_dstpath.touch()
        self.duplicate_rows_dstpath.touch()
        self.accepted_rows_dstpath.touch()

    def _format_row_w_struct_issue_for_logging(self, rownum: int, row: list[str], issue_description: str) -> str:
        """Return the log text for the given row with structural issue"""
        log_ncolumns = self.__largest_ncolumns + 2
        log_row = [rownum, *row] + ["" for _ in range(log_ncolumns)]
        log_row = log_row[:log_ncolumns]
        log_row[-1] = issue_description
        return ",".join(log_row) + "\n"

    def _update_ncolumns_info(self) -> None:
        """Update number of columns info"""
        self.__most_frequent_ncolumns = 0
        self.__largest_ncolumns = 0
        ncolumns_count: Dict[int, int] = {}
        with open(str(self.data_specification.uploaded_filepath)) as csvfile:
            line = csvfile.readline()
            ncolumns = len(line.split(self.data_specification.delimiter))
            ncolumns_count[ncolumns] += 1
            self.__largest_ncolumns = max(self.__largest_ncolumns, ncolumns)
        most_frequent_ncolumns = max(ncolumns_count, key=lambda x: ncolumns_count.get(x, -1))
        assert most_frequent_ncolumns != -1
        self.__most_frequent_ncolumns = most_frequent_ncolumns
