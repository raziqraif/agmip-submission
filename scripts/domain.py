from __future__ import annotations
from contextlib import redirect_stderr
from copy import copy
from copy import deepcopy
import csv
from datetime import datetime
import difflib
import io
from io import TextIOWrapper
import math
import numpy as np
import os
import pandas as pd
from pandas import DataFrame
from pathlib import Path
from typing import Optional, List, Dict, Set, Union, Tuple

from pandas.core.groupby.generic import DataFrameGroupBy


WORKINGDIR_PATH: Path = Path(__name__).parent.parent / "workingdir"  # <PROJECT_DIR>/workingdir
DOWNLOADDIR_PATH: Path = WORKINGDIR_PATH / "downloads"


class BadLabelInfo:
    """
    A value model to store information about a bad label
    A bad label is defined to be a label/field that does not follow the correct protocol but can be fixed
    automatically by the application

    NOTE: Because we override the __hash__ method, this class is not completely safe to be used with hashtable-based 
    data structure
    @date Aug 5, 2021
    """
    def __init__(self, label: str, associated_column: str, fix: str) -> None:
        self.label: str = label
        self.associated_column: str = associated_column
        self.fix: str = fix

    def __hash__(self) -> int:
        """
        Override hash operation to make sure two objects with the same attribute values produces the same hash

        NOTE: Whenever the attribute values change, the hash value will change as well. The consequence is, this class'
        instances require careful consideration when used with hashtable-based data structure like dict and set
        """
        return hash(self.label + self.associated_column + self.fix)

    def __eq__(self, obj) -> bool:
        """ Override equality operator for convenience """
        if not isinstance(obj, BadLabelInfo):
            return False
        return (self.label == obj.label) and (self.associated_column == obj.associated_column) and (self.fix == obj.fix) 


class UnknownLabelInfo:
    """
    A domain entity to store information about an unknown label
    A bad label is defined to be a label/field that does not follow the correct protocol but can be fixed
    automatically by the application
    
    NOTE: Because we override the __hash__ method, this class is not completely safe to be used with hashtable-based 
    data structure
    @date Aug 5, 2021
    """
    def __init__(self, label: str, associated_column: str, closest_match: str, fix: str, override: bool):
        self.label: str = label
        self.associated_column: str = associated_column
        self.closest_match: str = closest_match
        self.fix: str = fix
        self.override: bool = override
    
    def __hash__(self) -> int:
        """
        Override hash operation to make sure two objects with the same attribute values produces the same hash

        NOTE: Whenever the attribute values change, the hash value will change as well. The consequence is, this class'
        instances require careful consideration when used with hashtable-based data structure like dict and set
        """
        return hash(self.label + self.associated_column + self.closest_match + self.fix + str(self.override))

    def __eq__(self, obj) -> bool:
        """ Override equality operator for convenience """
        if not isinstance(obj, UnknownLabelInfo):
            return False
        return (self.label == obj.label) and (self.associated_column == obj.associated_column) and (self.closest_match == obj.closest_match) and (self.fix == obj.fix) and (self.override == obj.override)

    def __str__(self) -> str:
        return f"{self.label},{self.associated_column},{self.closest_match},{self.fix},{self.override}"


class InputDataEntity:
    """ 
    A domain entity that represents our input data/file
    It stores information that is required for parsing the input data and transforming the data columns into the correct 
    arrangement. It also provides several utilities to guess all this information and to get a preview of the parsed 
    input data.
    
    @date Aug 5, 2021
    """

    _NROWS_IN_SAMPLE_DATA = 1000

    def __init__(self):
        # Input format specification attributes
        self.model_name: str = ""
        self.header_is_included: bool = False
        self.scenarios_to_ignore: List[str] = []
        self._file_nrows = 0
        # Input format specification attributes & file path which will only be accessed via properties 
        # @date Aug 4, 2021
        self._file_path: Path = Path()
        self._delimiter: str = ""
        self._initial_lines_to_skip: int = 0
        # Column assignment attributes
        self.scenario_colnum: int = 0   # colnum -> column number (1-based indexing)
        self.region_colnum: int = 0
        self.variable_colnum: int = 0 
        self.item_colnum: int = 0
        self.unit_colnum: int = 0
        self.year_colnum: int = 0
        self.value_colnum: int = 0
        # Private attributes to help calculate sample parsed input data
        # NOTE: The reason we keep track of the "topmost" sample and a "nonskipped" sample was to avoid loading the 
        # whole file into memory. In retrospect, this is a premature optimization and could've been made 
        # simpler.  
        # TODO: Simplify the operations that require these two sample attributes
        # @date Aug 5, 2021
        self._input_data_topmost_sample: list[str] = []     # top X input data       
        self._input_data_nonskipped_sample: list[str] = []  # top X non-skipped input data
        self._sample_parsed_input_data_memo: Optional[list[list[str]]] = None

    @classmethod
    def create(cls, file_path: Path) -> InputDataEntity:
        """
        Create an instance of this class
        Return the created instance or raise an exception if an error occurred
        """
        entity = InputDataEntity()
        entity._file_path = file_path
        assert file_path.is_file()
        entity._input_data_topmost_sample = []
        entity._input_data_nonskipped_sample = []
        try:
            with open(str(file_path)) as csvfile:
                lines = csvfile.readlines()
                entity._file_nrows = len(lines)
                entity._input_data_topmost_sample = lines[: entity._NROWS_IN_SAMPLE_DATA]
                entity._input_data_nonskipped_sample = (
                    lines[entity.initial_lines_to_skip: entity.initial_lines_to_skip + entity._NROWS_IN_SAMPLE_DATA]
                    if entity.initial_lines_to_skip < entity._file_nrows 
                    else []
                )
        except:
            raise Exception("Error when opening file")
        return entity 

    def guess_delimiter(self, valid_delimiters: list[str]) -> bool:
        """Guess the delimiter from the sample input data and update the value
        Return True if the guess was successful, else False
        """
        sample = "\n".join(self._input_data_topmost_sample)
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
        sample = "\n".join(self._input_data_topmost_sample)
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
            row.split(self.delimiter) if len(self.delimiter) > 0 else [row] for row in self._input_data_topmost_sample
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
        if count > self._NROWS_IN_SAMPLE_DATA * 0.9:
            self.initial_lines_to_skip = 0
            return False
        self.initial_lines_to_skip = count
        return True

    def guess_model_name_n_column_assignments(self) -> bool:
        """
        Guess the model name and column assignments, and mutate the appropariate states
        Return True if some guesses were successful, else False
        """
        sample_parsed_csv_rows = self.sample_parsed_input_data
        nrows = len(sample_parsed_csv_rows)
        ncols = len(sample_parsed_csv_rows[0]) if nrows > 0 else 0
        if nrows == 0 or ncols == 0:
            return False
        quotes = '\'\"`'
        guessed_something = False
        for col_index in range(ncols):
            for row_index in range(nrows):
                cell_value = sample_parsed_csv_rows[row_index][col_index].strip(quotes)
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
        if DataRuleRepository.query_label_in_model_names(cell_value):
            self.model_name = cell_value
            return 0
        elif (cell_value == "Scenario") or DataRuleRepository.query_label_in_scenarios(cell_value):
            self.scenario_colnum = col_index + 1
            return 1
        elif (cell_value == "Region") or DataRuleRepository.query_label_in_regions(cell_value):
            self.region_colnum = col_index + 1
            return 2
        elif (cell_value == "Variable") or DataRuleRepository.query_label_in_variables(cell_value):
            self.variable_colnum = col_index + 1
            return 3
        elif (cell_value == "Item") or DataRuleRepository.query_label_in_items(cell_value):
            self.item_colnum = col_index + 1
            return 4
        elif (cell_value == "Unit") or DataRuleRepository.query_label_in_units(cell_value):
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
    def delimiter(self) -> str:
        return self._delimiter

    @delimiter.setter
    def delimiter(self, value: str) -> None:
        self._delimiter = value
        # Reset column assignments and the parsed input data sample
        self._sample_parsed_input_data_memo = None
        self.scenario_colnum = 0
        self.region_colnum = 0
        self.variable_colnum = 0
        self.item_colnum = 0
        self.unit_colnum = 0
        self.year_colnum = 0
        self.value_colnum = 0

    @property
    def file_path(self) -> Path:
        return self._file_path

    @property
    def initial_lines_to_skip(self) -> int:
        return self._initial_lines_to_skip

    @initial_lines_to_skip.setter
    def initial_lines_to_skip(self, value: int) -> None:
        assert value >= 0
        self._initial_lines_to_skip = value
        self._sample_parsed_input_data_memo = None
        # Reset column assignments if all file content was skipped
        if value > self._file_nrows:
            self.scenario_colnum = 0
            self.region_colnum = 0
            self.variable_colnum = 0
            self.item_colnum = 0
            self.unit_colnum = 0
            self.year_colnum = 0
            self.value_colnum = 0
        # Recompute input data sample
        if value == 0:
            self._input_data_nonskipped_sample = self._input_data_topmost_sample
            return
        self._input_data_nonskipped_sample = []
        try:
            with open(str(self.file_path)) as csvfile:
                lines = csvfile.readlines()
                self._input_data_topmost_sample = lines[: self._NROWS_IN_SAMPLE_DATA]
                self._input_data_nonskipped_sample = (
                    lines[self.initial_lines_to_skip: self.initial_lines_to_skip + self._NROWS_IN_SAMPLE_DATA]
                )
        except:
            return

    @property
    def sample_parsed_input_data(self) -> list[list[str]]:
        """
        Parse & process a subset of the raw input data and return the result

        The processing done is not exhaustive and only includes:
        - Skipping initial rows
        - Splitting rows based on the delimiter
        - Guessing the correct number of columns and removing rows with mismatched number of columns

        NOTE: This property will be queried by multiple dependents, so it's value is memoized to avoid
        recalculations.
        Every time this property's dependencies (like delimiter) is updated, the memo must be reset.
        @date 7/6/21
        """
        if self._sample_parsed_input_data_memo is not None:
            return self._sample_parsed_input_data_memo
        # Split rows in the sample input data
        rows = [
            row.split(self.delimiter) if self.delimiter != "" else [row] for row in self._input_data_nonskipped_sample
        ]
        # Return if input data has no rows
        if len(rows) == 0:
            self._sample_parsed_input_data_memo = rows
            return rows
        # Use the most frequent number of columns in the sample data as a proxy for the number of columns in a clean row
        # NOTE: If the number of dirty rows > number of clean rows, we will have incorrect result here
        # @date 6/23/21
        _ncolumns_bincount: np.ndarray = np.bincount([len(row) for row in rows])
        most_frequent_ncolumns = int(_ncolumns_bincount.argmax())  # type-casted to raise error for non-int values
        # Prune rows with mismatched columns
        rows = [row for row in rows if len(row) == most_frequent_ncolumns]
        self._sample_parsed_input_data_memo = rows
        return rows

    def __str__(self) -> str:
        return f"""
        > Input Data Entity
        File path = {str(self.file_path)}
        Model name = {self.model_name}
        Delimiter = {self.delimiter}
        Header is included = {self.header_is_included}
        Scenario colnum = {self.scenario_colnum} 
        Region colnum = {self.region_colnum} 
        Variable colnum = {self.variable_colnum} 
        Item colnum = {self.item_colnum} 
        Unit colnum = {self.unit_colnum} 
        Year colnum = {self.year_colnum} 
        Value colnum = {self.value_colnum} 
        """


class InputDataDiagnosis:
    """
    A domain entity to represent an input data diagnosis. 
    This class stores diagnosis results and provides some diagnosis utility methods.
    """

    _DOWNLOADDIR_PATH = WORKINGDIR_PATH / "downloads"
    # Column names used for reporting "associated columns" in bad labels table and unknown labels table
    SCENARIO_COLNAME = "Scenario"
    REGION_COLNAME = "Region"
    VARIABLE_COLNAME = "Variable"
    ITEM_COLNAME = "Item"
    UNIT_COLNAME = "Unit"
    YEAR_COLNAME = "Year"
    VALUE_COLNAME = "Value"
    # File destination paths of diagnosed rows 
    STRUCTISSUEROWS_DSTPATH = _DOWNLOADDIR_PATH / "Rows With Structural Issue.csv"
    DUPLICATESROWS_DSTPATH = _DOWNLOADDIR_PATH / "Duplicate Records.csv"
    IGNOREDSCENARIOROWS_DSTPATH = _DOWNLOADDIR_PATH / "Records With An Ignored Scenario.csv"
    ACCEPTEDROWS_DSTPATH = _DOWNLOADDIR_PATH / "Accepted Records.csv"

    def __init__(self) -> None:
        # Results of row checks
        self.nrows_w_struct_issue = 0
        self.nrows_w_ignored_scenario = 0
        self.nrows_duplicate = 0
        self.nrows_accepted = 0
        # Results of field checks
        self.bad_labels: List[BadLabelInfo] = [] # Labels that violate data protocol but can be fixed automatically
        self.unknown_labels: List[UnknownLabelInfo] = [] # Labels that violate data protocol but cannot be fixed automatically
        self.unknown_years: Set[str] = set()   # Valid years that do not exist in the data protocol yet. Needs to be included
        # into the data protocol file so that we can generate the appropriate GAMS header file later
        # Private helper attributes
        # - information about input file
        self._input_entity = InputDataEntity()
        self._correct_ncolumns = 0
        self._largest_ncolumns = 0
        # - row occurrence dictionary for duplicate checking
        self._row_occurence_dict: Dict[str, int] = {}

    @classmethod
    def create(cls, input_entity: InputDataEntity) -> InputDataDiagnosis:
        """
        Create an return an instance of this class
        
        To create the instance, we will diagnose the input data and populate the relevant attributes and files.

        In general, the diagnosis involves performing "row checks" on data rows and categorizing them as
        1. Rows with structural issue
        2. Rows with ignored scenario
        3. Duplicate rows
        4. Accepted rows
        Each of this group of rows will be logged into the appropriate destination file.

        For accepted rows, we will also perform "field checks" on their fields and try to find for
        1. "Bad" fields
        2. "Unknown" fields
        and log the result into the appropriate in-memory data structure.
        
        TODO: Reimplement this method with pandas for better performance (refer to the 
        _diagnosed_data_with_pandas_attempt() for existing attempt)

        TODO: Consider abstracting some functionalities in this class into a Factory class and a Service class
        @date Aug 5, 2021
        """
        diagnosis = InputDataDiagnosis()
        diagnosis._initialize_row_destination_files()
        diagnosis._input_entity = input_entity
        # Initialize sets to store found labels/fields
        scenario_fields: Set[str] = set()
        region_fields: Set[str] = set()
        variable_fields: Set[str] = set()
        item_fields: Set[str] = set()
        year_fields: Set[str] = set()
        unit_fields: Set[str] = set()
        # Initialize variables required to parse input file
        delimiter = input_entity.delimiter
        header_is_included = input_entity.header_is_included
        initial_lines_to_skip = input_entity.initial_lines_to_skip
        scenario_colidx = input_entity.scenario_colnum - 1
        region_colidx = input_entity.region_colnum - 1
        variable_colidx = input_entity.variable_colnum - 1
        item_colidx = input_entity.item_colnum - 1
        unit_colidx = input_entity.unit_colnum - 1
        year_colidx = input_entity.year_colnum - 1
        value_colidx = input_entity.value_colnum - 1
        # Update private helper attributes
        diagnosis._update_ncolumns_info(input_entity)
        # Open all row destination files 
        # fmt: off
        with \
            open(str(input_entity.file_path), "r") as inputfile, \
            open(str(diagnosis.STRUCTISSUEROWS_DSTPATH), "w+") as structissuefile, \
            open(str(diagnosis.IGNOREDSCENARIOROWS_DSTPATH), "w+") as ignoredscenfile, \
            open(str(diagnosis.DUPLICATESROWS_DSTPATH), "w+") as duplicatesfile, \
            open(str(diagnosis.ACCEPTEDROWS_DSTPATH), "w+") as acceptedfile \
        :
        # fmt: on
            # Get lines and ncolumns info from input file
            lines = inputfile.readlines()
            # Diagnose every line from the input file
            for line_index in range(len(lines)):
                line = lines[line_index].strip("\n")
                row = line.split(delimiter)
                rownum = line_index + 1
                # Ignore skipped row
                if rownum <= initial_lines_to_skip:
                    continue
                # Ignore header row
                if (rownum == initial_lines_to_skip + 1) and header_is_included:
                    continue
                # Ignore row that fails a row check
                if diagnosis._diagnose_row(rownum, row, line, structissuefile, ignoredscenfile, duplicatesfile):
                    continue
                # Log accepted row
                diagnosis.nrows_accepted += 1
                acceptedfile.write(line + "\n")
                # Store found labels/fields
                _quotes = '\'\"`'
                scenario_fields.add(row[scenario_colidx].strip(_quotes))
                region_fields.add(row[region_colidx].strip(_quotes))
                variable_fields.add(row[variable_colidx].strip(_quotes))
                item_fields.add(row[item_colidx].strip(_quotes))
                unit_fields.add(row[unit_colidx].strip(_quotes))
                year_fields.add(row[year_colidx].strip(_quotes))
                # Parse value
                diagnosis._diagnose_value_field(row[value_colidx].strip(_quotes))
        # Diagnose all found fields 
        for scenario in scenario_fields:
            diagnosis._diagnose_scenario_field(scenario)
        for region in region_fields:
            diagnosis._diagnose_region_field(region)
        for variable in variable_fields:
            diagnosis._diagnose_variable_field(variable)
        for item in item_fields:
            diagnosis._diagnose_item_field(item)
        for year in year_fields:
            diagnosis._diagnose_year_field(year)
        for unit in unit_fields:
            diagnosis._diagnose_unit_field(unit)
        # Remove duplicates from bad/unknown labels table
        # Note: the reason we did not simply store the labels in a set is because the label classes are not safe to
        # be used with hashtable-based data structure
        diagnosis.bad_labels = list(set(diagnosis.bad_labels))
        diagnosis.unknown_labels = list(set(diagnosis.unknown_labels))
        return diagnosis

    def add_rows_with_structural_issue(self) -> None:
        """
        Update diagnosis based on cleaned/processed data
        Reason: If unknown variables were fixed to a valid variable, its associated value was never compared against
        """
        pass
    # Private util methods for row checks

    def _diagnose_row(self, rownum: int, row: list[str], line: str, structissuefile: TextIOWrapper, ignoredscenfile: TextIOWrapper, duplicatesfile: TextIOWrapper) -> bool:
        """
        Check the given row for various issues
        If a row fails a check, then it will be logged into the appropriate file
        Return True if the row fails a check, else return False
        """
        if self._check_row_for_structural_issue(rownum, row, structissuefile):
            return True
        if self._check_row_for_ignored_scenario(rownum, row, ignoredscenfile):
            return True
        if self._check_if_duplicate_row(rownum, line, duplicatesfile):
            return True
        return False 
    
    def _check_row_for_structural_issue(self, rownum: int, row: list[str], structissuefile: TextIOWrapper) -> bool:
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
        if row[self._input_entity.scenario_colnum - 1] == "":
            self._log_row_w_struct_issue(rownum, row, "Empty scenario field", structissuefile)
            return True
        if row[self._input_entity.region_colnum - 1] == "":
            self._log_row_w_struct_issue(rownum, row, "Empty region field", structissuefile)
            return True
        if row[self._input_entity.variable_colnum - 1] == "":
            self._log_row_w_struct_issue(rownum, row, "Empty variable field", structissuefile)
            return True
        if row[self._input_entity.item_colnum - 1] == "":
            self._log_row_w_struct_issue(rownum, row, "Empty item field", structissuefile)
            return True
        if row[self._input_entity.unit_colnum - 1] == "":
            self._log_row_w_struct_issue(rownum, row, "Empty unit field", structissuefile)
            return True
        year_field = row[self._input_entity.year_colnum - 1]
        if year_field == "":
            self._log_row_w_struct_issue(rownum, row, "Empty year field", structissuefile)
            return True
        try:
            int(year_field)
        except:
            self._log_row_w_struct_issue(rownum, row, "Non-integer year field", structissuefile)
            return True
        if self._check_row_for_value_w_structural_issue(rownum, row, structissuefile):
            return True

        self.nrows_w_struct_issue -= 1  # Substract the value back if the row does not have a struc. issue
        return False

    def _check_row_for_value_w_structural_issue(self, rownum: int, row: list[str], structissuefile: TextIOWrapper) -> bool:
        """Check if row has a value field with a structural issue and log it if it does"""
        value_field = row[self._input_entity.value_colnum - 1]
        try:
            # Get fixed value
            value_fix = DataRuleRepository.query_fix_from_value_fix_table(value_field)
            value_fix = value_fix if value_fix is not None else value_field
            # Get matching variable 
            variable_field = row[self._input_entity.variable_colnum - 1]
            matching_variable = DataRuleRepository.query_matching_variable(variable_field)
            matching_variable = matching_variable if matching_variable is not None else variable_field
            # Get matching unit
            unit_field = row[self._input_entity.unit_colnum - 1]
            matching_unit = DataRuleRepository.query_matching_unit(unit_field)
            matching_unit = matching_unit if matching_unit is not None else unit_field 
            # Get min/max value for the given variable and unit
            min_value = DataRuleRepository.query_variable_min_value(matching_variable, matching_unit)
            max_value = DataRuleRepository.query_variable_max_value(matching_variable, matching_unit)
            if float(value_fix) < min_value:
                issue_text = "Value for variable {} is smaller than {} {}".format(matching_variable, min_value, matching_unit)
                self._log_row_w_struct_issue(rownum, row, issue_text, structissuefile)
                return True
            if float(value_fix) > max_value:
                issue_text = "Value for variable {} is greater than {} {}".format(matching_variable, max_value, matching_unit)
                self._log_row_w_struct_issue(rownum, row, issue_text, structissuefile)
                return True
        except:
            self._log_row_w_struct_issue(rownum, row, "Non-numeric value field", structissuefile)
            return True
        return False

    def _check_row_for_ignored_scenario(self, rownum: int, row: list[str], ignoredscenfile: TextIOWrapper) -> bool:
        """
        Check if a row contains an ignored scenario and logs it into the given file if it does.
        Returns the result of the check.
        """
        if row[self._input_entity.scenario_colnum - 1] in self._input_entity.scenarios_to_ignore:
            log_row = [str(rownum), *row]
            log_text = ",".join(log_row) + "\n"
            ignoredscenfile.write(log_text)
            self.nrows_w_ignored_scenario += 1
            return True
        return False

    def _check_if_duplicate_row(self, rownum: int, row: str, duplicatesfile: TextIOWrapper) -> bool:
        """
        Check if a row is a duplicate and log it into the duplicates file if it is.
        Return the result of the check.
        """
        # NOTE: Finding duplicates with the help of an in-memory data structure might cause a problem if the dataset
        # is too large. If that proves to be the case, consider using solutions like SQL
        # @date 7/7/2021
        self._row_occurence_dict.setdefault(row, 0)
        self._row_occurence_dict[row] += 1
        occurence = self._row_occurence_dict[row]
        if occurence > 1:
            log_text = "{},{},{}\n".format(rownum, row, occurence)
            duplicatesfile.write(log_text)
            self.nrows_duplicate += 1
            return True
        return False

    # Private util methods for field/label checks

    def _diagnose_value_field(self, value: str) -> None:
        """Checks if a value exists in the fix table and logs it if it does"""
        fixed_value = DataRuleRepository.query_fix_from_value_fix_table(value)
        if fixed_value is not None:
            float(fixed_value)  # Raise an error if it's non-numeric
            self._log_bad_label(value, self.VALUE_COLNAME, fixed_value)
        else:
            float(value)  # Raise an error if it's non-numeric

    def _diagnose_scenario_field(self, scenario: str) -> None:
        """Checks if a scenario is bad / unknown and logs it if it is"""
        scenario_w_correct_case = DataRuleRepository.query_matching_scenario(scenario)
        # Correct scenario
        if scenario_w_correct_case == scenario:
            return
        # Unkown scenario
        if scenario_w_correct_case is None:
            closest_scenario = DataRuleRepository.query_partially_matching_scenario(scenario)
            self._log_unknown_label(scenario, self.SCENARIO_COLNAME, closest_scenario)
            return
        # Known scenario but spelled wrongly
        if scenario_w_correct_case != scenario:
            self._log_bad_label(scenario, self.SCENARIO_COLNAME, scenario_w_correct_case)

    def _diagnose_region_field(self, region: str) -> None:
        """Check if a region is bad or unknown and logs it if it is"""
        region_w_correct_case = DataRuleRepository.query_matching_region(region)
        # Correct region
        if region_w_correct_case == region:
            return
        fixed_region = DataRuleRepository.query_fix_from_region_fix_table(region)
        # Unknown region
        if (region_w_correct_case is None) and (fixed_region is None):
            closest_region = DataRuleRepository.query_partially_matching_region(region)
            self._log_unknown_label(region, self.REGION_COLNAME, closest_region)
        # Known region but spelled wrongly
        elif (region_w_correct_case != region) and (region_w_correct_case is not None):
            self._log_bad_label(region, self.REGION_COLNAME, region_w_correct_case)
        # Known bad region 
        elif fixed_region is not None:
            self._log_bad_label(region, self.REGION_COLNAME, fixed_region)

    def _diagnose_variable_field(self, variable: str) -> None:
        """Check if a variable is bad or unknown and logs it if it is"""
        variable_w_correct_case = DataRuleRepository.query_matching_variable(variable)
        # Correct variable
        if variable_w_correct_case == variable:
            return
        # Unkown variable
        if variable_w_correct_case is None:
            closest_variable = DataRuleRepository.query_partially_matching_variable(variable)
            self._log_unknown_label(variable, self.VARIABLE_COLNAME, closest_variable)
            return
        # Known variable but spelled wrongly
        if variable_w_correct_case != variable:
            self._log_bad_label(variable, self.VARIABLE_COLNAME, variable_w_correct_case)

    def _diagnose_item_field(self, item: str) -> None:
        """Check if an item is bad or unknown and logs it if it is"""
        item_w_correct_case = DataRuleRepository.query_matching_item(item)
        # Correct item
        if item_w_correct_case == item:
            return
        # Unkown item
        if item_w_correct_case is None:
            closest_item = DataRuleRepository.query_partially_matching_item(item)
            self._log_unknown_label(item, self.ITEM_COLNAME, closest_item)
            return
        # Known item but spelled wrongly
        if item_w_correct_case != item:
            self._log_bad_label(item, self.ITEM_COLNAME, item_w_correct_case)

    def _diagnose_year_field(self, year: str) -> None:
        """Check if a year is bad or unknown and logs it if it is"""
        # NOTE: This method assumes that rows with non-integer year value would have failed the row structural check,
        # so the following type-cast should never raise an error
        int(year) 
        if not DataRuleRepository.query_label_in_years(year):
            self.unknown_years.add(year)  # Unknown years will be automatically recognized

    def _diagnose_unit_field(self, unit: str) -> None:
        """Check if an unit is bad or unknown and logs it if it is"""
        unit_w_correct_case = DataRuleRepository.query_matching_unit(unit)
        # Correct unit
        if unit_w_correct_case == unit:
            return
        # Unkown unit
        if unit_w_correct_case is None:
            closest_unit = DataRuleRepository.query_partially_matching_unit(unit)
            self._log_unknown_label(unit, self.UNIT_COLNAME, closest_unit)
            return
        # Known unit but spelled wrongly
        if unit_w_correct_case != unit:
            self._log_bad_label(unit, self.UNIT_COLNAME, unit_w_correct_case)

    # Private util methods to log found errors/issues

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
        self.bad_labels.append(BadLabelInfo(bad_label, associated_column, fix))

    def _log_unknown_label(self, unknown_label: str, associated_column: str, closest_label: str) -> None:
        """Logs unknown label"""
        # Appending row 1 by 1 to a pandas dataframe is slow, so we store these rows in a list first
        self.unknown_labels.append(UnknownLabelInfo(unknown_label, associated_column, closest_label, fix="", override=False))

    # Other private util methods

    def _initialize_row_destination_files(self):
        """Create/Recreate destination files"""
        # Deletes existing files, if any
        if self.STRUCTISSUEROWS_DSTPATH.exists():
            self.STRUCTISSUEROWS_DSTPATH.unlink()
        if self.IGNOREDSCENARIOROWS_DSTPATH.exists():
            self.IGNOREDSCENARIOROWS_DSTPATH.unlink()
        if self.DUPLICATESROWS_DSTPATH.exists():
            self.DUPLICATESROWS_DSTPATH.unlink()
        if self.ACCEPTEDROWS_DSTPATH.exists():
            self.ACCEPTEDROWS_DSTPATH.unlink()
        # Create files
        self.STRUCTISSUEROWS_DSTPATH.touch()
        self.IGNOREDSCENARIOROWS_DSTPATH.touch()
        self.DUPLICATESROWS_DSTPATH.touch()
        self.ACCEPTEDROWS_DSTPATH.touch()

    def _update_ncolumns_info(self, input_entity: InputDataEntity) -> None:
        """Get info about number of columns and populate the relevant private attributes"""
        self._correct_ncolumns = 0
        largest_ncolumns = 0
        ncolumns_occurence_dict: Dict[int, int] = {}
        with open(str(input_entity.file_path)) as csvfile:
            lines = csvfile.readlines()
            for line in lines:
                ncolumns = len(line.split(input_entity.delimiter))
                ncolumns_occurence_dict.setdefault(ncolumns, 0)
                ncolumns_occurence_dict[ncolumns] += 1
                largest_ncolumns = max(largest_ncolumns, ncolumns)
        most_frequent_ncolumns = max(ncolumns_occurence_dict, key=lambda x: ncolumns_occurence_dict.get(x, -1))
        assert most_frequent_ncolumns != -1
        # Use most frequent ncolumns as a proxy for the number of columns in a clean row
        self._correct_ncolumns = most_frequent_ncolumns
        self._largest_ncolumns = largest_ncolumns

    # Attempt to reimplement diagnose_data() with pandas

    def _diagnose_data_with_pandas_attempt(self, input_entity: InputDataEntity) -> None:
        """
        Attempt to reimplement parse data with pandas to gain better performance (WORK-IN-PROGRESS)
        TODO: Complete or reimplement this method
        """
        error_buffer = io.StringIO()
        with redirect_stderr(error_buffer):
            dataframe = pd.read_csv(
                input_entity.file_path, 
                skiprows=input_entity.initial_lines_to_skip, 
                header=0 if input_entity.header_is_included else None,   # type: ignore
                error_bad_lines=False, 
                warn_bad_lines=True, 
                na_filter=False
            )
        assert isinstance(dataframe, pd.DataFrame)
        # Get important column names
        _colnames = dataframe.columns
        rownum_colname = "Row Number"
        dataframe[rownum_colname] = dataframe.index
        scenario_colname = _colnames[input_entity.scenario_colnum - 1]
        region_colname = _colnames[input_entity.region_colnum - 1]
        variable_colname = _colnames[input_entity.variable_colnum - 1]
        item_colname = _colnames[input_entity.item_colnum - 1]
        year_colname = _colnames[input_entity.year_colnum - 1]
        value_colname = _colnames[input_entity.value_colnum - 1]
        unit_colname = _colnames[input_entity.unit_colnum - 1]
        # Add new utility columns to help with filtering
        matchingvar_colname = "Matching Variable"
        fixedval_colname = "Fixed Value"
        minval_colname = "Minimum Value"
        maxval_colname = "Maximum Value"
        dataframe[matchingvar_colname] = dataframe[variable_colname].apply(lambda x: DataRuleRepository.query_matching_variable(x) if DataRuleRepository.query_matching_variable(x) is not None else x)
        dataframe[fixedval_colname] = dataframe[value_colname].apply(lambda x: self._get_fixed_value_or_dummy_value(x))
        dataframe[minval_colname] = dataframe.apply(lambda x: DataRuleRepository.query_variable_min_value(x[variable_colname], x[unit_colname]))
        dataframe[maxval_colname] = dataframe.apply(lambda x: DataRuleRepository.query_variable_max_value(x[variable_colname], x[unit_colname]))
        # Reassign coltypes
        dataframe[scenario_colname] = dataframe[scenario_colname].apply(str)  
        dataframe[region_colname] = dataframe[region_colname].apply(str)
        dataframe[variable_colname] = dataframe[variable_colname].apply(str)
        dataframe[item_colname] = dataframe[item_colname].apply(str)
        dataframe[year_colname] = dataframe[year_colname].apply(str).apply(str)  # TODO: Will this affect performance?
        dataframe[value_colname] = dataframe[value_colname].apply(str)
        dataframe[unit_colname] = dataframe[unit_colname].apply(str)
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
        # Filter duplicate records
        duplicates_df = _remaining_df[_remaining_df.duplicated()]  
        assert duplicates_df    
        # TODO: build dataframes for rows with ignored scenario and accepted rows, and log them into a file
        # make sure to maintain the existing granularity level when logging the rows

    def _get_fixed_value_or_dummy_value(self, value: str) -> float:
        """Helper method for parse_data() implemented in pandas"""
        fix = DataRuleRepository.query_fix_from_value_fix_table(value)
        fix = fix if fix is not None else value 
        try: 
            return float(fix)
        except:
            return 0


class OutputDataEntity:
    """Domain entity for our processed/output data"""
    
    # Column names of the pandas dataframe that stores our processed data
    MODEL_COLNAME: str = "Model name"
    SCENARIO_COLNAME: str = "Scenario"
    REGION_COLNAME: str = "Region"
    VARIABLE_COLNAME: str = "Variable"
    ITEM_COLNAME: str = "Item"
    UNIT_COLNAME: str = "Unit"
    YEAR_COLNAME: str = "Year"
    VALUE_COLNAME: str = "Value"

    def __init__(self) -> None:
        self.file_path: Path = Path()
        # A pandas dataframe that store our processed data
        # Data frame specification
        # 1. follows the column arrangement dictated by the GlobalEcon team
        # 2. uses class attributes defined above as column names
        # 3. stores columns with numeric type in str, and the rest as categorical dtype.
        # @date Aug 5, 2021
        self.processed_data: pd.DataFrame = DataFrame()
        # Unique fields in the processed dataframe (sorted)
        self.unique_scenarios: List[str] = []
        self.unique_regions: List[str] = []
        self.unique_variables: List[str] = []
        self.unique_items: List[str] = []
        self.unique_years: List[str] = []

    def get_value_trends_table(self, scenario: str, region: str, variable: str) -> Optional[DataFrameGroupBy]:
        """
        Return a table for value trends visualization or None
        The table will be built from our processed data, and the arguments provided specify how the processed data
        should be sliced.
        """
        processed_data = self.processed_data
        # Slice & copy data frame based on arguments
        sliced_data = processed_data.loc[
            (processed_data[self.SCENARIO_COLNAME] == scenario)
            & (processed_data[self.REGION_COLNAME] == region)
            & (processed_data[self.VARIABLE_COLNAME] == variable)
        ].copy()
        # Return if sliced data is empty
        if sliced_data.shape[0] == 0:
            self.valuetrends_viz_table = None
            return
        # Convert year and value column to numeric
        sliced_data[self.YEAR_COLNAME] = pd.to_numeric(sliced_data[self.YEAR_COLNAME])
        sliced_data[self.VALUE_COLNAME] = pd.to_numeric(sliced_data[self.VALUE_COLNAME])
        return sliced_data.groupby(self.ITEM_COLNAME)
 
    def get_growth_trends_table(self, scenario: str, region: str, variable: str) -> Optional[DataFrameGroupBy]:
        """
        Return a table for growth trends visualization or None
        The table will be built from our processed data, and the arguments provided specify how the processed data
        should be sliced.

        # TODO: Implement this method
        """
        processed_data = self.processed_data
        # Slice & copy data frame based on arguments
        sliced_data = processed_data.loc[
            (processed_data[self.SCENARIO_COLNAME] == scenario)
            & (processed_data[self.REGION_COLNAME] == region)
            & (processed_data[self.VARIABLE_COLNAME] == variable)
        ].copy()
        # Return if sliced data is empty
        if sliced_data.shape[0] == 0:
            self.valuetrends_viz_table = None
            return
        # Convert year and value column to numeric
        sliced_data[self.YEAR_COLNAME] = pd.to_numeric(sliced_data[self.YEAR_COLNAME])
        sliced_data[self.VALUE_COLNAME] = pd.to_numeric(sliced_data[self.VALUE_COLNAME])
        return sliced_data.groupby(self.ITEM_COLNAME)

    @classmethod
    def create(cls, input_entity: InputDataEntity, input_diagnosis: InputDataDiagnosis) -> OutputDataEntity:
        """
        Create and return an instance of this class
        TODO: Consider abstracting some functionalities in this class into a Factory class and a Service class
        """
        # Read from accepted rows destination file
        # The file should have no header row or lines to skip, and should not have records with any row issues, but 
        # may still contain records with fixable field issues. The records in this file should also not have additional
        # or removed columns. 
        # @ date  Aug 5, 2021
        processed_data = pd.read_csv(input_diagnosis.ACCEPTEDROWS_DSTPATH, delimiter=input_entity.delimiter, header=None, dtype=object) # type: ignore
        # Make sure the data frame has all the required 8 columns (not more) in the correct arrangement
        colnames = processed_data.columns
        colnames = [
            colnames[input_entity.scenario_colnum - 1],
            colnames[input_entity.region_colnum - 1],
            colnames[input_entity.variable_colnum - 1],
            colnames[input_entity.item_colnum - 1],
            colnames[input_entity.unit_colnum - 1],
            colnames[input_entity.year_colnum - 1],
            colnames[input_entity.value_colnum - 1],
        ]
        processed_data = processed_data[colnames]
        processed_data.insert(0, cls.MODEL_COLNAME, input_entity.model_name)
        # Rename data frame columns 
        processed_data.columns = [
            cls.MODEL_COLNAME, 
            cls.SCENARIO_COLNAME,
            cls.REGION_COLNAME,
            cls.VARIABLE_COLNAME,
            cls.ITEM_COLNAME,
            cls.UNIT_COLNAME,
            cls.YEAR_COLNAME, 
            cls.VALUE_COLNAME
        ]
        # Reassign column dtypes 
        # Note: numeric columns are stored as str because we might have values like NA, N/A, #DIV/0! etc
        processed_data[cls.SCENARIO_COLNAME] = processed_data[cls.SCENARIO_COLNAME].astype("category")  
        processed_data[cls.REGION_COLNAME] = processed_data[cls.REGION_COLNAME].astype("category")  
        processed_data[cls.VARIABLE_COLNAME] = processed_data[cls.VARIABLE_COLNAME].astype("category")  
        processed_data[cls.ITEM_COLNAME] = processed_data[cls.ITEM_COLNAME].astype("category")
        processed_data[cls.YEAR_COLNAME] = processed_data[cls.YEAR_COLNAME].apply(str)  # TODO: Will this affect performance?
        processed_data[cls.VALUE_COLNAME] = processed_data[cls.VALUE_COLNAME].apply(str)
        processed_data[cls.UNIT_COLNAME] = processed_data[cls.UNIT_COLNAME].astype("category")
        # Bad / unknown label mapping dictionaries
        scenariomapping = {}
        regionmapping = {}
        variablemapping = {}
        itemmapping = {}
        unitmapping = {}
        yearmapping = {}
        valuemapping = {}
        # Dropped labels set
        droppedscenarios = set()
        droppedregions = set()
        droppedvariables = set()
        droppeditems = set()
        droppedyears = set()
        droppedunits = set()
        droppedvalues = set()
        # Populate the label mapping dictionaries based on the info about bad labels
        for bad_label_info in input_diagnosis.bad_labels:
            label = bad_label_info.label
            associatedcol = bad_label_info.associated_column
            fix = bad_label_info.fix
            if associatedcol == input_diagnosis.SCENARIO_COLNAME:
                scenariomapping[label] = fix
            elif associatedcol == input_diagnosis.REGION_COLNAME:
                regionmapping[label] = fix
            elif associatedcol == input_diagnosis.VARIABLE_COLNAME:
                variablemapping[label] = fix
            elif associatedcol == input_diagnosis.ITEM_COLNAME:
                itemmapping[label] = fix
            elif associatedcol == input_diagnosis.UNIT_COLNAME:
                unitmapping[label] = fix
            elif associatedcol == input_diagnosis.YEAR_COLNAME:
                yearmapping[label] = fix
            elif associatedcol == input_diagnosis.VALUE_COLNAME:
                valuemapping[label] = fix
        # Populate the label mapping dictionaries and dropped labels set based on the info about unknown labels
        for unknown_label_info in input_diagnosis.unknown_labels:
            label = unknown_label_info.label
            associatedcol = unknown_label_info.associated_column
            fix = unknown_label_info.fix
            override = unknown_label_info.override
            assert not ((fix != "") and override)   # Assert that the label is not selected to be both fixed and overridden
            if fix != "":
                # Remember fixes
                if associatedcol == input_diagnosis.SCENARIO_COLNAME:
                    scenariomapping[label] = fix
                elif associatedcol == input_diagnosis.REGION_COLNAME:
                    regionmapping[label] = fix
                elif associatedcol == input_diagnosis.VARIABLE_COLNAME:
                    variablemapping[label] = fix
                elif associatedcol == input_diagnosis.ITEM_COLNAME:
                    itemmapping[label] = fix
                elif associatedcol == input_diagnosis.UNIT_COLNAME:
                    unitmapping[label] = fix
                elif associatedcol == input_diagnosis.YEAR_COLNAME:
                    yearmapping[label] = fix
                elif associatedcol == input_diagnosis.VALUE_COLNAME:
                    valuemapping[label] = fix
            elif not override:
                # Remember labels to be dropped
                if associatedcol == input_diagnosis.SCENARIO_COLNAME:
                    droppedscenarios.add(label)
                elif associatedcol == input_diagnosis.REGION_COLNAME:
                    droppedregions.add(label)
                elif associatedcol == input_diagnosis.VARIABLE_COLNAME:
                    droppedvariables.add(label)
                elif associatedcol == input_diagnosis.ITEM_COLNAME:
                    droppeditems.add(label)
                elif associatedcol == input_diagnosis.YEAR_COLNAME:
                    droppedyears.add(label)
                elif associatedcol == input_diagnosis.UNIT_COLNAME:
                    droppedunits.add(label)
                elif associatedcol == input_diagnosis.VALUE_COLNAME:
                    droppedvalues.add(label)
        # Apply label fixes 
        processed_data[cls.SCENARIO_COLNAME] = processed_data[cls.SCENARIO_COLNAME].apply(lambda x: scenariomapping[x] if x in scenariomapping.keys() else x)
        processed_data[cls.REGION_COLNAME] = processed_data[cls.REGION_COLNAME].apply(lambda x: regionmapping[x] if x in regionmapping.keys() else x)
        processed_data[cls.VARIABLE_COLNAME] = processed_data[cls.VARIABLE_COLNAME].apply(lambda x: variablemapping[x] if x in variablemapping.keys() else x)
        processed_data[cls.ITEM_COLNAME] = processed_data[cls.ITEM_COLNAME].apply(lambda x: itemmapping[x] if x in itemmapping.keys() else x)
        processed_data[cls.UNIT_COLNAME] = processed_data[cls.UNIT_COLNAME].apply(lambda x: unitmapping[x] if x in unitmapping.keys() else x)
        processed_data[cls.YEAR_COLNAME] = processed_data[cls.YEAR_COLNAME].apply(lambda x: unitmapping[x] if x in unitmapping.keys() else x)
        processed_data[cls.VALUE_COLNAME] = processed_data[cls.VALUE_COLNAME].apply(lambda x: valuemapping[x] if x in valuemapping.keys() else x)
        # Drop records containing dropped labels
        processed_data = processed_data[processed_data[cls.SCENARIO_COLNAME].apply(lambda x: x not in droppedscenarios)]
        processed_data = processed_data[processed_data[cls.REGION_COLNAME].apply(lambda x: x not in droppedregions)]
        processed_data = processed_data[processed_data[cls.VARIABLE_COLNAME].apply(lambda x: x not in droppedvariables)]
        processed_data = processed_data[processed_data[cls.ITEM_COLNAME].apply(lambda x: x not in droppeditems)]
        processed_data = processed_data[processed_data[cls.YEAR_COLNAME].apply(lambda x: x not in droppedyears)]
        processed_data = processed_data[processed_data[cls.UNIT_COLNAME].apply(lambda x: x not in droppedunits)]
        processed_data = processed_data[processed_data[cls.VALUE_COLNAME].apply(lambda x: x not in droppedvalues)]
        # Create entity
        output_entity = OutputDataEntity()
        output_entity.processed_data = processed_data
        output_entity.file_path = DOWNLOADDIR_PATH / (
            Path(input_entity.file_path).stem + datetime.now().strftime("_%m%d%Y_%H%M%S").upper() + ".csv"
        )
        # Store processed data in a downloadable file
        processed_data.to_csv(output_entity.file_path, header=False, index=False)
        # Populate list of unique fields
        cls._populate_unique_fields(output_entity)
        # Return
        return output_entity

    @classmethod
    def _populate_unique_fields(cls, output_entity: OutputDataEntity) -> None:
        """"
        Populate the lists of unique fields retrieved from the processed data frame. 
        Each list must be sorted.
        NOTE: Some of the data frame columns have categorical data type, which cannot be sorted right away, so we convert
        these columns into ndarrays first.
        @Aug 5, 2021
        """
        output_entity.unique_scenarios = np.asarray(output_entity.processed_data[output_entity.SCENARIO_COLNAME].unique()).tolist()
        output_entity.unique_scenarios.sort()
        output_entity.unique_regions = np.asarray(output_entity.processed_data[output_entity.REGION_COLNAME].unique()).tolist()
        output_entity.unique_regions.sort()
        output_entity.unique_variables = np.asarray(output_entity.processed_data[output_entity.VARIABLE_COLNAME].unique()).tolist()
        output_entity.unique_variables.sort()
        output_entity.unique_items = np.asarray(output_entity.processed_data[output_entity.ITEM_COLNAME].unique()).tolist()
        output_entity.unique_items.sort()
        output_entity.unique_years = np.asarray(output_entity.processed_data[output_entity.YEAR_COLNAME].unique()).tolist()
        output_entity.unique_years.sort()
        output_entity.unique_years = np.asarray(output_entity.processed_data[output_entity.UNIT_COLNAME].unique()).tolist()
        output_entity.unique_years.sort()


class DataRuleRepository:
    """
    Provide interfaces to interact with the spreadsheet that stores our data formatting rules

    NOTE: It seems like the "proper" domain-driven approach is to place a Repository object in a higher layer 
    and use dependency inversion pattern to access it from the domain layer, but such complexity seems unnecessary 
    given the current project requirement.
    @date Aug 5, 2021
    """

    DATA_RULES_SPREADSHEET_PATH: Path = WORKINGDIR_PATH / "RuleTables.xlsx"

    # Spreadsheet containing labels information
    __spreadsheet: Dict[str, DataFrame] = pd.read_excel(
        str(DATA_RULES_SPREADSHEET_PATH),
        engine="openpyxl",
        sheet_name=None,
        keep_default_na=False,
    )
    # Valid labels table
    _model_table = __spreadsheet["ModelTable"]
    _scenario_table = __spreadsheet["ScenarioTable"]
    _region_table = __spreadsheet["RegionTable"]
    _variable_table = __spreadsheet["VariableTable"]
    _item_table = __spreadsheet["ItemTable"]
    _unit_table = __spreadsheet["UnitTable"]
    _year_table = __spreadsheet["YearTable"]
    # Fix tables
    _regionfix_table = __spreadsheet["RegionFixTable"]
    _valuefix_table = __spreadsheet["ValueFixTable"]
    # Constraint tables
    __variableunitvalue_table = __spreadsheet["VariableUnitValueTable"]
    # Valid columns
    _model_names = set(_model_table["Model"].astype("str"))
    _scenarios = set(_scenario_table["Scenario"].astype("str"))
    _regions = set(_region_table["Region"].astype("str"))
    _variables = set(_variable_table["Variable"].astype("str"))
    _items = set(_item_table["Item"].astype("str"))
    _units = set(_unit_table["Unit"].astype("str"))
    _years = set(_year_table["Year"].astype("str"))
    # Data structure for critical queries
    _matchingunit_memo: Dict[str, str] = {}
    _matchingvariable_memo: Dict[str, str] = {}
    _valuefix_memo: Dict[str, str] = dict(_valuefix_table.iloc[:, 1:].values)  # Load dataframe as dict
    _variable_minvalue_memo: Dict[Tuple[str, str], float] = {}
    _variable_maxvalue_memo: Dict[Tuple[str, str], float] = {}
    # Populate data structures for critical queries
    # - Populate matching unit memo
    for unit in _units:
        _matchingunit_memo[unit.lower()] = unit 
    # - Populate matching variable memo
    for variable in _variables:
        _matchingvariable_memo[variable.lower()] = variable
    # - Populate value-fix memo
    for key in _valuefix_memo.keys():
        _valuefix_memo[key] = str(_valuefix_memo[key])  # store numbers as strings
    # - Populate variable's min/max value memo
    for namedtuple in __variableunitvalue_table.itertuples(index=False):
        # Get required variables
        variable = namedtuple.Variable
        unit = namedtuple.Unit
        minvalue = namedtuple[__variableunitvalue_table.columns.get_loc("Minimum Value")]
        maxvalue = namedtuple[__variableunitvalue_table.columns.get_loc("Maximum Value")]
        # Update memo
        _variable_minvalue_memo[(variable, unit)] = minvalue
        _variable_maxvalue_memo[(variable, unit)] = maxvalue

    @classmethod
    def query_model_names(cls) -> List[str]:
        """Get all valid model names"""
        result = list(cls._model_names)
        result.sort()
        return result

    @classmethod
    def query_scenarios(cls) -> List[str]:
        """Get all valid scenarios"""
        result = list(cls._scenarios)
        result.sort()
        return result

    @classmethod
    def query_regions(cls) -> List[str]:
        """Get all valid regions"""
        result = list(cls._regions)
        result.sort()
        return result

    @classmethod
    def query_variables(cls) -> List[str]:
        """Get all valid variables"""
        result = list(cls._variables)
        result.sort()
        return result

    @classmethod
    def query_items(cls) -> List[str]:
        """Get all valid items """
        result = list(cls._items)
        result.sort()
        return result

    @classmethod
    def query_units(cls) -> List[str]:
        """Get all valid units """
        result = list(cls._units)
        result.sort()
        return result

    @classmethod
    def query_label_in_model_names(cls, label: str) -> bool:
        """Check if the argument exists in the model name table"""
        return label in cls._model_names

    @classmethod
    def query_label_in_scenarios(cls, label: str) -> bool:
        """Check if the argument exists in the scenario table"""
        return label in cls._scenarios

    @classmethod
    def query_label_in_regions(cls, label: str) -> bool:
        """Check if the argument exists in the region table"""
        return label in cls._regions

    @classmethod
    def query_label_in_variables(cls, label: str) -> bool:
        """Check if the argument exists in the variable table"""
        return label in cls._variables

    @classmethod
    def query_label_in_items(cls, label: str) -> bool:
        """Check if the argument exists in the item table"""
        return label in cls._items

    @classmethod
    def query_label_in_units(cls, label: str) -> bool:
        """Check if the argument exists in the unit table"""
        return label in cls._units

    @classmethod
    def query_label_in_years(cls, label: str) -> bool:
        """Check if the argument exists in the years table"""
        return label in cls._years

    @classmethod
    def query_matching_scenario(cls, scenario: str) -> Optional[str]:
        """Returns a scenario with the exact case-insensitive spelling as the argument, or None"""
        scenario = scenario.lower()
        table = cls._scenario_table
        table = table[table["Scenario"].str.lower() == scenario]
        assert table.shape[0] <= 1
        if table.shape[0] != 0:
            return str(table.iloc[0]["Scenario"])  # type: ignore
        return None

    @classmethod
    def query_partially_matching_scenario(cls, scenario: str) -> str:
        """Returns a scenario with the closest spelling to the argument"""
        matches = difflib.get_close_matches(scenario, cls._scenarios, n=1, cutoff=0)
        assert len(matches) != 0
        return matches[0]

    @classmethod
    def query_matching_region(cls, region: str) -> Optional[str]:
        """Returns a region with the exact case-insensitive spelling as the argument, or None"""
        region = region.lower()
        table = cls._region_table
        table = table[table["Region"].str.lower() == region]
        assert table.shape[0] <= 1
        if table.shape[0] != 0:
            return str(table.iloc[0]["Region"])  # type: ignore
        return None

    @classmethod
    def query_partially_matching_region(cls, region: str) -> str:
        """Returns a region with the closest spelling to the argument"""
        matches = difflib.get_close_matches(region, cls._regions, n=1, cutoff=0)
        assert len(matches) != 0
        return matches[0]

    @classmethod
    def query_matching_variable(cls, variable: str) -> Optional[str]:
        """Returns a variable with the exact case-insensitive spelling as the argument, or None"""
        variable = variable.lower()
        try:
            return cls._matchingvariable_memo[variable]
        except:
            return None

    @classmethod
    def query_partially_matching_variable(cls, variable: str) -> str:
        """Returns a variable with the closest spelling to the argument"""
        matches = difflib.get_close_matches(variable, cls._variables, n=1, cutoff=0)
        assert len(matches) != 0
        return matches[0]

    @classmethod
    def query_matching_item(cls, item: str) -> Optional[str]:
        """Returns an item with the exact case-insensitive spelling as the argument, or None"""
        item = item.lower()
        table = cls._item_table
        table = table[table["Item"].str.lower() == item]
        assert table.shape[0] <= 1
        if table.shape[0] != 0:
            return str(table.iloc[0]["Item"])  # type: ignore
        return None

    @classmethod
    def query_partially_matching_item(cls, item: str) -> str:
        """Returns a item with the closest spelling to the argument"""
        matches = difflib.get_close_matches(item, cls._items, n=1, cutoff=0)
        assert len(matches) != 0
        return matches[0]

    @classmethod
    def query_matching_unit(cls, unit: str) -> Optional[str]:
        """Returns an unit with the exact case-insensitive spelling as the argument, or None"""
        unit = unit.lower()
        try:
            return cls._matchingunit_memo[unit]
        except:
            return None

    @classmethod
    def query_partially_matching_unit(cls, unit: str) -> str:
        """Returns a unit with the closest spelling to the argument"""
        matches = difflib.get_close_matches(unit, cls._units, n=1, cutoff=0)
        assert len(matches) != 0
        return matches[0]

    @classmethod
    def query_fix_from_value_fix_table(cls, value: str) -> Optional[str]:
        """Checks if a fix exists in the fix table and returns it. Returns None otherwise."""
        fix_table = cls._valuefix_memo
        try:
            return fix_table[value.lower()]
        except:
            return None

    @classmethod
    def query_fix_from_region_fix_table(cls, region: str) -> Optional[str]:
        """Checks if a fix exists in the fix table and returns it. Returns None otherwise."""
        fix_table = cls._regionfix_table
        # Get all rows containing the fix
        fix_table = fix_table[fix_table["Region"] == region.lower()]
        assert fix_table.shape[0] <= 1
        # Fix was found
        if fix_table.shape[0] != 0:
            return str(fix_table.iloc[0]["Fix"])
        return None

    @classmethod
    def query_variable_min_value(cls, variable: str, unit: str) -> float:
        """Return the minimum value for a variable"""
        if (variable, unit) in cls._variable_minvalue_memo.keys():
            return float(cls._variable_minvalue_memo[(variable, unit)])
        else:
            return -math.inf

    @classmethod
    def query_variable_max_value(cls, variable: str, unit: str) -> float:
        """Return the maximum value for a variable"""
        if (variable, unit) in cls._variable_maxvalue_memo.keys():
            return float(cls._variable_maxvalue_memo[(variable, unit)])
        else:
            return +math.inf
