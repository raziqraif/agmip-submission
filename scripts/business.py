from __future__ import annotations
from copy import copy
import csv
from io import DEFAULT_BUFFER_SIZE
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Optional, List

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
        if cell_value in LabelGateway.valid_model_names:
            self.model_name = cell_value
            return 0
        elif cell_value in LabelGateway.valid_scenarios:
            self.scenario_colnum = col_index + 1
            return 1
        elif cell_value in LabelGateway.valid_regions:
            self.region_colnum = col_index + 1
            return 2
        elif cell_value in LabelGateway.valid_variables:
            self.variable_colnum = col_index + 1
            return 3
        elif cell_value in LabelGateway.valid_items:
            self.item_colnum = col_index + 1
            return 4
        elif cell_value in LabelGateway.valid_units:
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


class IntegrityCheckService:
    """
    Service class for the integrity checking page
    @date July 5, 2021
    """

    def __init__(self):
        pass
