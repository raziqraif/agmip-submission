from __future__ import annotations
from contextlib import redirect_stderr
from copy import copy
from copy import deepcopy
import csv
import io
from io import TextIOWrapper
import numpy as np
import os
import pandas as pd
from pathlib import Path
from typing import Optional, List, Dict, Set

from .labelgateway import LabelGateway
pd.read_csv 

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
        self.scenario_colnum = 0
        self.region_colnum = 0
        self.variable_colnum = 0
        self.item_colnum = 0
        self.unit_colnum = 0
        self.year_colnum = 0
        self.value_colnum = 0

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
                lines = csvfile.readlines()
                self.__input_data_topmost_sample = lines[: self.SAMPLE_NROWS]
                self.__input_data_nonskipped_sample = (
                    lines[self.initial_lines_to_skip: self.initial_lines_to_skip + self.SAMPLE_NROWS]
                )
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
                lines = csvfile.readlines()
                self.__input_data_topmost_sample = lines[: self.SAMPLE_NROWS]
                self.__input_data_nonskipped_sample = (
                    lines[self.initial_lines_to_skip: self.initial_lines_to_skip + self.SAMPLE_NROWS]
                )
                self.__file_nrows = len(lines)
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
        elif (cell_value == "Scenario") or LabelGateway.query_label_in_scenarios(cell_value):
            self.scenario_colnum = col_index + 1
            return 1
        elif (cell_value == "Region") or LabelGateway.query_label_in_regions(cell_value):
            self.region_colnum = col_index + 1
            return 2
        elif (cell_value == "Variable") or LabelGateway.query_label_in_variables(cell_value):
            self.variable_colnum = col_index + 1
            return 3
        elif (cell_value == "Item") or LabelGateway.query_label_in_items(cell_value):
            self.item_colnum = col_index + 1
            return 4
        elif (cell_value == "Unit") or LabelGateway.query_label_in_units(cell_value):
            self.unit_colnum = col_index + 1
            return 5
        try:
            # Reminder: int(<float value in str repr>) will raise an error
            if (1000 < int(cell_value)) and (int(cell_value) < 9999):
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
    BAD_LABELS_TABLE_COLTITLES = ["Label", "Associated Column", "Fix"]
    UNKNOWN_LABELS_TABLE_COLTITLES = ["Label", "Associated Column", "Closest Match", "Fix", "Override"]

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
        self.rows_w_ignored_scenario_dstpath = self.WORKING_DIRPATH / "RecordsWithIgnoredScenario.csv"
        self.rows_w_struct_issue_dstpath = self.WORKING_DIRPATH / "RowsWithStructuralIssue.csv"
        # Label tables
        self.bad_labels_table = pd.DataFrame(columns=self.BAD_LABELS_TABLE_COLTITLES)
        self.unknown_labels_table = pd.DataFrame(columns=self.UNKNOWN_LABELS_TABLE_COLTITLES)
        # Util structures for labels
        self._bad_labels_list = []
        self._unknown_labels_list = []
        self._unknown_years: list[str] = []  # Unknown years will be added into the rule table automatically
        # Number of columns info
        self._correct_ncolumns = 0
        self._largest_ncolumns = 0
        # Duplicate check helper
        self.__row_occurence_dict: Dict[str, int] = {}
        # Actions
        self._initialize_files()
        self._update_ncolumns_info()

    def _parse_data(self) -> None:
        """Parse data in pandas"""
        error_buffer = io.StringIO()
        with redirect_stderr(error_buffer):
            dataframe = pd.read_csv(
                self.data_specification.uploaded_filepath, 
                skiprows=self.data_specification.initial_lines_to_skip, 
                header=0 if self.data_specification.header_is_included else None,   # type: ignore
                error_bad_lines=False, 
                warn_bad_lines=True, 
                na_filter=False
            )
        assert isinstance(dataframe, pd.DataFrame)
        # Get important column names
        _colnames = dataframe.columns
        rownum_colname = "Row Number"
        dataframe[rownum_colname] = dataframe.index
        scenario_colname = _colnames[self.data_specification.scenario_colnum - 1]
        region_colname = _colnames[self.data_specification.region_colnum - 1]
        variable_colname = _colnames[self.data_specification.variable_colnum - 1]
        item_colname = _colnames[self.data_specification.item_colnum - 1]
        year_colname = _colnames[self.data_specification.year_colnum - 1]
        value_colname = _colnames[self.data_specification.value_colnum - 1]
        unit_colname = _colnames[self.data_specification.unit_colnum - 1]
        # Add new utility columns to help with filtering
        matchingvar_colname = "Matching Variable"
        fixedval_colname = "Fixed Value"
        minval_colname = "Minimum Value"
        maxval_colname = "Maximum Value"
        dataframe[matchingvar_colname] = dataframe[variable_colname].apply(lambda x: LabelGateway.query_matching_variable(x) if LabelGateway.query_matching_variable(x) is not None else x)
        dataframe[fixedval_colname] = dataframe[value_colname].apply(lambda x: self._get_fixed_value_or_dummy_value(x))
        dataframe[minval_colname] = dataframe[variable_colname].apply(lambda x: LabelGateway.query_variable_min_value(x))
        dataframe[maxval_colname] = dataframe[variable_colname].apply(lambda x: LabelGateway.query_variable_max_value(x))
        # Reassign coltypes
        dataframe[scenario_colname] = dataframe[scenario_colname].astype("category")  
        dataframe[region_colname] = dataframe[region_colname].astype("category")  
        dataframe[variable_colname] = dataframe[variable_colname].astype("category")  
        dataframe[item_colname] = dataframe[item_colname].astype("category")
        dataframe[year_colname] = dataframe[year_colname].apply(str)  # TODO: Will this affect performance?
        dataframe[value_colname] = dataframe[value_colname].apply(str)
        dataframe[unit_colname] = dataframe[unit_colname].astype("category")
        # Filter records with structural issue
        _emptyscenario_df = dataframe[dataframe[scenario_colname] == ""]
        _remaining_df = dataframe[dataframe[scenario_colname] != ""]
        rows_w_structissues = _emptyscenario_df
        _emptyregion_df = _remaining_df[_remaining_df[region_colname] == ""]
        _remaining_df = _remaining_df[_remaining_df[region_colname] != ""]
        rows_w_structissues = rows_w_structissues.merge(_emptyregion_df)
        _emptyvariable_df = _remaining_df[_remaining_df[variable_colname] == ""]
        _remaining_df = _remaining_df[_remaining_df[variable_colname] != ""]
        rows_w_structissues = rows_w_structissues.merge(_emptyvariable_df)
        _emptyitem_df = _remaining_df[_remaining_df[item_colname] == ""]
        _remaining_df = _remaining_df[_remaining_df[item_colname] != ""]
        rows_w_structissues = rows_w_structissues.merge(_emptyitem_df)
        _emptyunit_df = _remaining_df[_remaining_df[unit_colname] == ""]
        _remaining_df = _remaining_df[_remaining_df[unit_colname] != ""]
        rows_w_structissues = rows_w_structissues.merge(_emptyunit_df)
        _emptyyear_df = _remaining_df[_remaining_df[year_colname] == ""]
        _remaining_df = _remaining_df[_remaining_df[year_colname] != ""]
        rows_w_structissues = rows_w_structissues.merge(_emptyyear_df)
        _nonintegeryear_df = _remaining_df[~_remaining_df[year_colname].apply(lambda x: x.isdecimal())]
        _remaining_df = _remaining_df[_remaining_df[year_colname].apply(lambda x: x.isdecimal())]
        rows_w_structissues = rows_w_structissues.merge(_nonintegeryear_df)
        _valuetoosmall_df = _remaining_df.apply(lambda x: x[fixedval_colname] < x[minval_colname], axis=1)
        _remaining_df = _remaining_df.apply(lambda x: x[fixedval_colname] > x[minval_colname], axis=1)
        rows_w_structissues = rows_w_structissues.merge(_valuetoosmall_df)
        _valuetoolarge_df = _remaining_df.apply(lambda x: x[fixedval_colname] > x[maxval_colname], axis=1)
        _remaining_df = _remaining_df.apply(lambda x: x[fixedval_colname] < x[maxval_colname], axis=1)
        rows_w_structissues = rows_w_structissues.merge(_valuetoolarge_df)
        rows_w_structissues.drop_duplicates()
        self.nrows_w_struct_issue = rows_w_structissues.shape[0]
        print(_remaining_df)
        # Get duplicate records
        duplicates_df = _remaining_df[_remaining_df.duplicated()]  
        # TODO: Make each df disjoint
        duplicates_df.to_csv(self.duplicate_rows_dstpath)
        # self.rows_w_field_issues = pd.DataFrame(_rows_w_field_issues)
        # self.rows_w_ignored_scenario = pd.DataFrame(_rows_w_ignored_scenario)
        # self.duplicate_rows = _remaining_rows[_remaining_rows.duplicated(subset=KEY_COLUMNS)]
        # self.accepted_rows = _remaining_rows.drop_duplicates(subset=KEY_COLUMNS)

    def _get_fixed_value_or_dummy_value(self, value: str) -> float:
        fix = LabelGateway.query_fix_from_value_fix_table(value)
        fix = fix if fix is not None else value 
        try: 
            return float(fix)
        except:
            return 0


    def parse_data(self) -> None:   # NOSONAR 
        """Parse data and populate destination files, nrows attributes, and label tables"""
        self.__init__(self.data_specification)  # Reset all attributes
        # Initialize sets to store found labels
        scenarios: Set[str] = set()
        regions: Set[str] = set()
        variables: Set[str] = set()
        items: Set[str] = set()
        years: Set[str] = set()
        units: Set[str] = set()
        # Open data file and all destination files and start parsing data
        # fmt: off
        with \
            open(str(self.data_specification.uploaded_filepath)) as datafile, \
            open(str(self.rows_w_struct_issue_dstpath), "w+") as structissuefile, \
            open(str(self.rows_w_ignored_scenario_dstpath), "w+") as ignoredscenfile, \
            open(str(self.duplicate_rows_dstpath), "w+") as duplicatesfile, \
            open(str(self.accepted_rows_dstpath), "w+") as acceptedfile \
        :
        # fmt: on
            delimiter = self.data_specification.delimiter
            scenario_colidx = self.data_specification.scenario_colnum - 1
            region_colidx = self.data_specification.region_colnum - 1
            variable_colidx = self.data_specification.variable_colnum - 1
            item_colidx = self.data_specification.item_colnum - 1
            unit_colidx = self.data_specification.unit_colnum - 1
            year_colidx = self.data_specification.year_colnum - 1
            value_colidx = self.data_specification.value_colnum - 1
            for line_idx, line in enumerate(datafile):
                line = line[:-1] if line[-1] == "\n" else line
                rownum = line_idx + 1
                row = line.split(delimiter)
                if (rownum == 1) and self.data_specification.header_is_included:
                    continue
                # Check and filter rows with various issues
                if self.check_for_structural_issue(rownum, row, structissuefile):
                    continue
                # 14 s
                if self.check_for_ignored_scenario(rownum, row, ignoredscenfile):
                    continue
                # 16 s
                if self.check_if_duplicate(rownum, line, duplicatesfile):
                    continue
                # 19.6
                # Log accepted row
                self.nrows_accepted += 1
                acceptedfile.write(line)
                # 23.5
                # Store found labels
                scenarios.add(row[scenario_colidx])
                regions.add(row[region_colidx])
                variables.add(row[variable_colidx])
                items.add(row[item_colidx])
                units.add(row[unit_colidx])
                years.add(row[year_colidx])
                # 28.9
                # Parse value
                self.parse_value_field(row[value_colidx])
        # Parse all found labels
        for scenario in scenarios:
            self.parse_scenario_field(scenario)
        for region in regions:
            self.parse_region_field(region)
        for variable in variables:
            self.parse_variable_field(variable)
        for item in items:
            self.parse_item_field(item)
        for year in years:
            self.parse_year_field(year)
        for unit in units:
            self.parse_unit_field(unit)
        # Populate bad / unknown labels table
        self.bad_labels_table = pd.DataFrame(self._bad_labels_list, columns=self.BAD_LABELS_TABLE_COLTITLES)
        self.unknown_labels_table = pd.DataFrame(self._unknown_labels_list, columns=self.UNKNOWN_LABELS_TABLE_COLTITLES)

    def check_for_structural_issue(self, rownum: int, row: list[str], structissuefile: TextIOWrapper) -> bool:
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
        self.nrows_w_struct_issue += 1  # Assume the row has a structural issue
        if len(row) != self._correct_ncolumns:
            self._log_row_w_struct_issue(rownum, row, "Mismatched number of fields", structissuefile)
            return True
        if row[self.data_specification.scenario_colnum - 1] == "":
            self._log_row_w_struct_issue(rownum, row, "Empty scenario field", structissuefile)
            return True
        if row[self.data_specification.region_colnum - 1] == "":
            self._log_row_w_struct_issue(rownum, row, "Empty region field", structissuefile)
            return True
        if row[self.data_specification.variable_colnum - 1] == "":
            self._log_row_w_struct_issue(rownum, row, "Empty variable field", structissuefile)
            return True
        if row[self.data_specification.item_colnum - 1] == "":
            self._log_row_w_struct_issue(rownum, row, "Empty item field", structissuefile)
            return True
        if row[self.data_specification.unit_colnum - 1] == "":
            self._log_row_w_struct_issue(rownum, row, "Empty unit field", structissuefile)
            return True
        year_field = row[self.data_specification.year_colnum - 1]
        if year_field == "":
            self._log_row_w_struct_issue(rownum, row, "Empty year field", structissuefile)
            return True
        try:
            int(year_field)
        except:
            self._log_row_w_struct_issue(rownum, row, "Non-integer year field", structissuefile)
            return True
        if self._check_for_value_w_structural_issue(rownum, row, structissuefile):
            return True

        self.nrows_w_struct_issue -= 1  # Substract the value back if the row does not have a struc. issue
        return False

    def _check_for_value_w_structural_issue(self, rownum: int, row: list[str], structissuefile: TextIOWrapper) -> bool:
        """Check if row has a value field with a structural issue and log it if it does"""
        value_field = row[self.data_specification.value_colnum - 1]
        try:
            value_fix = LabelGateway.query_fix_from_value_fix_table(value_field)
            value_fix = value_fix if value_fix is not None else value_field
            variable_field = row[self.data_specification.variable_colnum - 1]
            matching_variable = LabelGateway.query_matching_variable(variable_field)
            matching_variable = matching_variable if matching_variable is not None else variable_field
            min_value = LabelGateway.query_variable_min_value(matching_variable)
            max_value = LabelGateway.query_variable_max_value(matching_variable)
            if float(value_fix) < min_value:
                issue_text = "Value for variable {} is too small".format(matching_variable)
                self._log_row_w_struct_issue(rownum, row, issue_text, structissuefile)
                return True
            if float(value_fix) > max_value:
                issue_text = "Value for variable {} is too large".format(matching_variable)
                self._log_row_w_struct_issue(rownum, row, issue_text, structissuefile)
                return True
        except:
            self._log_row_w_struct_issue(rownum, row, "Non-numeric value field", structissuefile)
            return True
        return False

    def check_for_ignored_scenario(self, rownum: int, row: list[str], ignoredscenfile: TextIOWrapper) -> bool:
        """
        Check if a row contains an ignored scenario and logs it into the given file if it does.
        Returns the result of the check.
        """
        if row[self.data_specification.scenario_colnum - 1] in self.data_specification.scenarios_to_ignore:
            log_row = [str(rownum), *row]
            log_text = ",".join(log_row) + "\n"
            ignoredscenfile.write(log_text)
            self.nrows_w_ignored_scenario += 1
            return True
        return False

    def check_if_duplicate(self, rownum: int, row: str, duplicatesfile: TextIOWrapper) -> bool:
        """
        Check if a row is a duplicate and log it into the duplicates file if it is.
        Return the result of the check.
        """
        # NOTE: Finding duplicates with the help of an in-memory data structure might cause a problem if the dataset
        # is too large. If that proves to be the case, consider using solutions like SQL
        # @date 7/7/2021
        self.__row_occurence_dict.setdefault(row, 0)
        self.__row_occurence_dict[row] += 1
        occurence = self.__row_occurence_dict[row]
        if occurence > 1:
            log_text = "{},{},{}\n".format(rownum, row, occurence)
            duplicatesfile.write(log_text)
            self.nrows_duplicate += 1
            return True
        return False

    def parse_value_field(self, value: str) -> None:
        """Checks if a value exists in the fix table and logs it if it does"""
        fixed_value = LabelGateway.query_fix_from_value_fix_table(value)
        if fixed_value is not None:
            float(fixed_value)  # Raise an error if it's non-numeric
            self._log_bad_label(value, "Value", fixed_value)
        else:
            float(value)  # Raise an error if it's non-numeric

    def parse_scenario_field(self, scenario: str) -> None:
        """Checks if a scenario is bad / unknown and logs it if it is"""
        scenario_w_correct_case = LabelGateway.query_matching_scenario(scenario)
        # Correct scenario
        if scenario_w_correct_case == scenario:
            return
        # Unkown scenario
        if scenario_w_correct_case is None:
            closest_scenario = LabelGateway.query_partially_matching_scenario(scenario)
            self._log_unknown_label(scenario, "Scenario", closest_scenario)
            return
        # Known scenario but spelled wrongly
        if scenario_w_correct_case != scenario:
            self._log_bad_label(scenario, "Scenario", scenario_w_correct_case)

    def parse_region_field(self, region: str) -> None:
        """Check if a region is bad or unknown and logs it if it is"""
        region_w_correct_case = LabelGateway.query_matching_region(region)
        # Correct region
        if region_w_correct_case == region:
            return
        fixed_region = LabelGateway.query_fix_from_region_fix_table(region)
        # Unkown region
        if (region_w_correct_case is None) and (fixed_region is None):
            closest_region = LabelGateway.query_partially_matching_region(region)
            self._log_unknown_label(region, "Region", closest_region)
            return
        # Known region but spelled wrongly
        if (region_w_correct_case != region) and (region_w_correct_case is not None):
            self._log_bad_label(region, "Region", region_w_correct_case)

    def parse_variable_field(self, variable: str) -> None:
        """Check if a variable is bad or unknown and logs it if it is"""
        variable_w_correct_case = LabelGateway.query_matching_variable(variable)
        # Correct variable
        if variable_w_correct_case == variable:
            return
        # Unkown variable
        if variable_w_correct_case is None:
            closest_variable = LabelGateway.query_partially_matching_variable(variable)
            self._log_unknown_label(variable, "Variable", closest_variable)
            return
        # Known variable but spelled wrongly
        if variable_w_correct_case != variable:
            self._log_bad_label(variable, "Variable", variable_w_correct_case)

    def parse_item_field(self, item: str) -> None:
        """Check if an item is bad or unknown and logs it if it is"""
        item_w_correct_case = LabelGateway.query_matching_item(item)
        # Correct item
        if item_w_correct_case == item:
            return
        # Unkown item
        if item_w_correct_case is None:
            closest_item = LabelGateway.query_partially_matching_item(item)
            self._log_unknown_label(item, "Item", closest_item)
            return
        # Known item but spelled wrongly
        if item_w_correct_case != item:
            self._log_bad_label(item, "Item", item_w_correct_case)

    def parse_year_field(self, year: str) -> None:
        """Check if a year is bad or unknown and logs it if it is"""
        if not LabelGateway.query_label_in_years(year):
            self._unknown_years.append(year)  # Unknown years will be automatically recognized

    def parse_unit_field(self, unit: str) -> None:
        """Check if an unit is bad or unknown and logs it if it is"""
        unit_w_correct_case = LabelGateway.query_matching_unit(unit)
        # Correct unit
        if unit_w_correct_case == unit:
            return
        # Unkown unit
        if unit_w_correct_case is None:
            closest_unit = LabelGateway.query_partially_matching_unit(unit)
            self._log_unknown_label(unit, "Unit", closest_unit)
            return
        # Known unit but spelled wrongly
        if unit_w_correct_case != unit:
            self._log_bad_label(unit, "Unit", unit_w_correct_case)

    def _initialize_files(self):
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

    def _update_ncolumns_info(self) -> None:
        """Update number of columns info"""
        self._correct_ncolumns = 0
        self._largest_ncolumns = self._correct_ncolumns
        ncolumns_count: Dict[int, int] = {}
        with open(str(self.data_specification.uploaded_filepath)) as csvfile:
            line = csvfile.readline()       # TODO: Fix 
            ncolumns = len(line.split(self.data_specification.delimiter))
            ncolumns_count.setdefault(ncolumns, 0)
            ncolumns_count[ncolumns] += 1
            self._largest_ncolumns = max(self._largest_ncolumns, ncolumns)
        most_frequent_ncolumns = max(ncolumns_count, key=lambda x: ncolumns_count.get(x, -1))
        assert most_frequent_ncolumns != -1
        self._correct_ncolumns = most_frequent_ncolumns

    def _log_row_w_struct_issue(self, rownum: int, row: list[str], issue_description: str, structissuefile: TextIOWrapper) -> None:
        """Return the log text for the given row with structural issue"""
        log_ncolumns = self._largest_ncolumns + 2
        log_row = [str(rownum), *row] + ["" for _ in range(log_ncolumns)]
        log_row = log_row[:log_ncolumns]
        log_row[-1] = issue_description
        log_text = ",".join(log_row) + "\n"
        structissuefile.write(log_text)

    def _log_bad_label(self, bad_label: str, associated_column: str, fix: str) -> None:
        """Logs bad label"""
        # Appending row 1 by 1 to a pandas dataframe is slow, so we store these rows in a list first
        self._bad_labels_list.append([bad_label, associated_column, fix])

    def _log_unknown_label(self, unknown_label: str, associated_column: str, closest_label: str) -> None:
        """Logs unknown label"""
        # Appending row 1 by 1 to a pandas dataframe is slow, so we store these rows in a list first
        self._unknown_labels_list.append([unknown_label, associated_column, closest_label, "", False])





