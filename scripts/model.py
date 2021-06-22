from __future__ import annotations  # Delay the evaluation of undefined types
import csv
import os
from pathlib import Path
import traceback
from typing import Any, Callable, Optional

import numpy as np
import pandas as pd

from .view import Delimiter


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
    UPLOAD_DIR: Path = Path(__name__).parent.parent / Path("uploads")  # <PROJECT_DIR>/uploads

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
        self.model_names: list[str] = ["Model 1", "Model 2", "Model 3"]
        self.scenarios: list[str] = ["SSP2_NoMt_NoCC_FlexA_DEV"]
        self.regions: list[str] = ["CAN"]
        self.variables: list[str] = ["CONS"]
        self.items: list[str] = ["RIC"]
        self.units: list[str] = ["1000 t dm"]
        self.years: list[str] = ["2010"]
        self.model_name: str = ""
        self._delimiter: str = ""
        self.header_is_included: bool = False
        self._lines_to_skip_str: str = "0"
        self.scenarios_to_ignore: str = ""
        self._assigned_colnum_for_scenario: int = 0
        self._assigned_colnum_for_region: int = 0
        self._assigned_colnum_for_variable: int = 0
        self._assigned_colnum_for_item: int = 0
        self._assigned_colnum_for_unit: int = 0
        self._assigned_colnum_for_year: int = 0
        self._assigned_colnum_for_value: int = 0
        self.raw_csv_rows: list[str] = []  # "raw" -> each row is not separated by the csv delimiter yet
        self.csv_rows: list[list[str]] = []
        self.most_frequent_ncolumn: int = 0
        self.rows_with_mismatched_ncolumn: list[list[str]] = []
        # Directory setup
        self.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

    def build_csv_rows(self):
        if len(self.raw_csv_rows) == 0:
            return
        try:
            lines_to_skip = int(self.lines_to_skip_str)
        except:
            lines_to_skip = 0

        if self.delimiter == "":
            self.csv_rows = [[row] for row in self.raw_csv_rows]
        else:
            self.csv_rows = [row.split(self.delimiter) for row in self.raw_csv_rows]
        ncolumns = np.array([len(row) for row in self.csv_rows])
        self.most_frequent_ncolumn = np.bincount(ncolumns).argmax()

    @property
    def delimiter(self) -> str:
        return self._delimiter

    @delimiter.setter
    def delimiter(self, value: str) -> None:
        assert value in Delimiter.get_models() or value == ""
        self._delimiter = value
        self._assigned_colnum_for_scenario = 0
        self._assigned_colnum_for_region = 0
        self._assigned_colnum_for_variable = 0
        self._assigned_colnum_for_item = 0
        self._assigned_colnum_for_unit = 0
        self._assigned_colnum_for_year = 0
        self._assigned_colnum_for_value = 0
        self.build_csv_rows()

    @property
    def lines_to_skip_str(self) -> str:
        return self._lines_to_skip_str

    @lines_to_skip_str.setter
    def lines_to_skip_str(self, value: str) -> None:
        try:
            lines_to_skip = int(value)  # convert float or int string to int
            self.lines_to_skip_str = str(lines_to_skip)
            if lines_to_skip >= len(self.csv_rows):
                self._assigned_colnum_for_scenario = 0
                self._assigned_colnum_for_region = 0
                self._assigned_colnum_for_variable = 0
                self._assigned_colnum_for_item = 0
                self._assigned_colnum_for_unit = 0
                self._assigned_colnum_for_year = 0
                self._assigned_colnum_for_value = 0
        except:
            self._lines_to_skip_str = value

    @property
    def column_options(self) -> list[str]:
        return list(self.uploaded_data_preview_content[0])

    @property
    def assigned_scenario_column(self) -> str:
        return ("", *self.column_options)[self._assigned_colnum_for_scenario]

    @assigned_scenario_column.setter
    def assigned_scenario_column(self, value: str):
        self._assigned_colnum_for_scenario = ([""] + self.column_options).index(value)

    @property
    def assigned_region_column(self) -> str:
        return ([""] + self.column_options)[self._assigned_colnum_for_region]

    @assigned_region_column.setter
    def assigned_region_column(self, value: str):
        self._assigned_colnum_for_region = ([""] + self.column_options).index(value)

    @property
    def assigned_variable_column(self) -> str:
        return ([""] + self.column_options)[self._assigned_colnum_for_variable]

    @assigned_variable_column.setter
    def assigned_variable_column(self, value: str):
        self._assigned_colnum_for_variable = ([""] + self.column_options).index(value)

    @property
    def assigned_item_column(self) -> str:
        return ([""] + self.column_options)[self._assigned_colnum_for_item]

    @assigned_item_column.setter
    def assigned_item_column(self, value: str):
        self._assigned_colnum_for_item = ([""] + self.column_options).index(value)

    @property
    def assigned_unit_column(self) -> str:
        return ([""] + self.column_options)[self._assigned_colnum_for_unit]

    @assigned_unit_column.setter
    def assigned_unit_column(self, value: str) -> None:
        self._assigned_colnum_for_unit = ([""] + self.column_options).index(value)

    @property
    def assigned_year_column(self) -> str:
        return ([""] + self.column_options)[self._assigned_colnum_for_year]

    @assigned_year_column.setter
    def assigned_year_column(self, value: str) -> None:
        self._assigned_colnum_for_year = ([""] + self.column_options).index(value)

    @property
    def assigned_value_column(self) -> str:
        return ([""] + self.column_options)[self._assigned_colnum_for_value]

    @assigned_value_column.setter
    def assigned_value_column(self, value: str) -> None:
        self._assigned_colnum_for_value = ([""] + self.column_options).index(value)

    @property
    def uploaded_data_preview_content(self) -> np.ndarray:
        """Return preview table content in a 2D ndarray"""
        # Get constants
        DEFAULT_CONTENT = np.array(["" for _ in range(24)]).reshape((3, 8)) 
        try:
            LINES_TO_SKIP = int(self.lines_to_skip_str) 
        except ValueError:
            LINES_TO_SKIP = 0
        if (len(self.csv_rows) == 0) or (LINES_TO_SKIP >= len(self.csv_rows)):
            return DEFAULT_CONTENT
        # Process table content 
        preview_table = []
        for row_index in range(LINES_TO_SKIP, len(self.csv_rows)):
            row = self.csv_rows[row_index]
            if len(row) == self.most_frequent_ncolumn:  # row's ncolumn is correct
                preview_table.append(row)
            if len(preview_table) == 3:
                break
        if self.header_is_included:
            preview_table[0] = [
                # Prepend column titles with a), b), c), d) ...
                chr(colnum + 97) + ")  " + preview_table[0][colnum]
                for colnum in range(len(preview_table[0]))
            ]
        else:
            assert self.most_frequent_ncolumn is not None
            header = ["Column " + str(i + 1) for i in range(self.most_frequent_ncolumn)]
            preview_table = [header] + preview_table[:2]
        return np.array(preview_table)

    @property
    def output_data_preview_content(self) -> np.ndarray:
        """Return preview table content in a 2d ndarray"""
        model_col = ["Model", self.model_name, self.model_name]
        # Lambda function to return a column content, given the title and column assignment
        get_column_content: Callable[[str, int], list[str]] = (
            lambda title, assigned_colnum: [title, "", ""]
            if assigned_colnum == 0
            else [title] + [self.uploaded_data_preview_content[row][assigned_colnum - 1] for row in (1, 2)]
        )
        # Get the content of all columns
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

    def intro(self, view: View, controller: Controller) -> None:  # type: ignore # noqa
        """Introduce MVC modules to each other"""
        self.view = view
        self.controller = controller

    def init_data_specification_states(self, file_name: str) -> Optional[str]:
        """
        Do necessary steps when entering the data specification page (only when it had just become active)
        Note that the page may become active / inactive multiple times.
        Returns an error message if an error is encountered, else None
        """
        assert len(file_name) > 0
        # Initialize data specification states
        self.model_name = ""
        self.delimiter = ""  # Note that the setter property will initialize some other states as well
        self.header_is_included = False
        self.lines_to_skip_str = "0"
        self.scenarios_to_ignore = ""
        self.raw_csv_rows = []
        self.csv_rows = []
        self.most_frequent_ncolumn = 0
        # Read file content and sniff the CSV format
        file_path = self.UPLOAD_DIR / Path(file_name)
        assert file_path.is_file()
        try:
            # Read file content
            with open(str(file_path)) as csvfile:
                self.raw_csv_rows = csvfile.readlines()
            # Sniff the csv format
            sample_data = "\n".join(self.raw_csv_rows[:1000])  # use X rows as sample data
            delimiters = "".join(Delimiter.get_models())
            format_sniffer = csv.Sniffer()
            csv_dialect = format_sniffer.sniff(sample_data, delimiters=delimiters)
            header_is_included = format_sniffer.has_header(sample_data)
        except csv.Error:  # Could be due to empty file, not enough sample data, etc
            return "Could not infer the CSV format"
        except IOError:
            return "Errror when opening file"
        except:
            traceback.print_exc()
            return "Unexpected error when loading file"
        # Update data specification states based on sniffed format
        self.model_name = "Model 1"
        self._delimiter = csv_dialect.delimiter
        self.header_is_included = header_is_included
        self.csv_rows = [row.split(self.delimiter) for row in self.raw_csv_rows]
        self.most_frequent_ncolumn = np.bincount([len(row) for row in self.csv_rows]).argmax()
        for row_index in range(len(self.csv_rows)):  # Guess the number of lines to skip
            self.lines_to_skip_str = str(row_index)
            if len(self.csv_rows[row_index]) == self.most_frequent_ncolumn:  # Number of column is correct
                break
        for col_index in range(self.most_frequent_ncolumn):  # Guess the column assignments
            for row_index in range(1000):  # Limit search to X rows
                if row_index > len(self.csv_rows):
                    break
                if len(self.csv_rows[row_index]) != self.most_frequent_ncolumn:  # Ignore dirty row
                    continue
                cell = self.csv_rows[row_index][col_index]
                if cell in self.model_names:
                    self.model_name = cell
                    break
                if cell in self.scenarios:
                    self._assigned_colnum_for_scenario = col_index + 1
                    break
                if cell in self.regions:
                    self._assigned_colnum_for_region = col_index + 1
                    break
                if cell in self.variables:
                    self._assigned_colnum_for_variable = col_index + 1
                    break
                if cell in self.items:
                    self._assigned_colnum_for_item = col_index + 1
                    break
                if cell in self.units:
                    self._assigned_colnum_for_unit = col_index + 1
                    break
                if cell in self.years:
                    self._assigned_colnum_for_year = col_index + 1
                    break
                try:
                    float(cell)
                    self._assigned_colnum_for_value = col_index + 1
                except ValueError:
                    pass
        return None

    def remove_file(self, file_name: str) -> None:
        """Remove uploaded file from the upload directory"""
        assert len(file_name) > 0
        file_path = self.UPLOAD_DIR / Path(file_name)
        assert file_path.is_file()
        file_path.unlink()
