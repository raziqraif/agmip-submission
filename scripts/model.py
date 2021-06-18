from __future__ import annotations  # Delay the evaluation of undefined types
import os
from pathlib import Path
from typing import Any, Optional, Union

import csv
import numpy as np
from numpy.core.fromnumeric import var
import pandas as pd
import traceback

from .view import Delimiter


def get_notebook_auth_token() -> str:
    """Get auth token to interact with notebook server's API"""

    # Terminal command to print the urls of running servers.
    stream = os.popen("jupyter notebook list")
    output = stream.read()

    # Assume our server is at the top of the output and extract its token

    # Format of output is "...http://SERVER_URL/?token=TOKEN :: ..."
    output = output.split("token=")[1]

    # Format of output is "TOKEN :: ..."
    token = output.split(" ")[0]
    return token


class JSAppModel:
    def __init__(self):
        # Auth token of notebook server
        self.nbserver_auth_token: str = get_notebook_auth_token()

        # Model ID of the label in "UA" (upload area) which displays the most recently uploaded file name.
        # This label is actually hidden and only used for communication between js & python.
        self.ua_file_label_model_id: str = ""

    def serialize(self) -> str:
        """Serialize self into a format that can be embedded into the Javascript context"""
        return str(vars(self))


class DataSpecificationInput:
    def __init__(self):
        """
        Note that for all attributes:
        None -> Empty input and was never modified by the user
        "" -> Empty input but was previously modified by the user
        """
        self.model_name: str = ""
        self.delimiter: str = ""
        self.header_is_included: bool = False
        self.lines_to_skip: str = "0"
        self.scenarios_to_ignore: str = ""
        self.scenario_column: str = ""
        self.scenario_column_number: int = 0
        self.region_column: str = ""
        self.region_column_number: int = 0
        self.variable_column: str = ""
        self.variable_column_number: int = 0
        self.item_column: str = ""
        self.item_column_number: int = 0
        self.unit_column: str = ""
        self.unit_column_number: int = 0
        self.year_column: str = ""
        self.year_column_number: int = 0
        self.value_column: str = ""
        self.value_column_number: int = 0


class Model:
    UPLOAD_DIR: Path = Path(__name__).parent.parent / Path("uploads")  # <PROJECT_DIR>/uploads

    def __init__(self):
        # Import MVC classes here to prevent circular import problem
        from .controller import Controller
        from .view import View

        self.view: View
        self.controller: Controller

        self.javascript_model = JSAppModel()
        self.finished_steps = 0
        self.uploaded_filename: str = ""  # Tracks uploaded file name
        # Needs to be updated when the file was removed too

        # Data specification-related attributes
        self.data_specification: DataSpecificationInput = DataSpecificationInput()
        self.raw_csv_rows: Optional[
            list[str]
        ] = None  # raw here means that each row was not separated by the csv delimiter yet
        self.csv_rows: Optional[list[list[str]]] = None
        self.most_frequent_ncolumn: Optional[int] = None
        self.rows_with_mismatched_ncolumn: Optional[list[list[str]]]
        self.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

    def rebuild_csv_rows(self):
        if self.delimiter == "":
            self.csv_rows = [[row] for row in self.raw_csv_rows]
        else:
            self.csv_rows = [row.split(self.delimiter) for row in self.raw_csv_rows]
        ncolumns = np.array([len(row) for row in self.csv_rows])
        self.most_frequent_ncolumn = np.bincount(ncolumns).argmax()

    @property
    def model_names(self) -> list[str]:
        return ["Model 1", "Model 2", "Model 3"]

    @property
    def model_name(self) -> str:
        return self.data_specification.model_name

    @property
    def delimiter(self) -> str:
        return self.data_specification.delimiter

    @delimiter.setter
    def delimiter(self, value: str) -> None:
        assert value in Delimiter.get_models() or value == ""
        self.data_specification.delimiter = value
        self.data_specification.scenario_column_number = 0
        self.data_specification.region_column_number = 0
        self.data_specification.variable_column_number = 0
        self.data_specification.item_column_number = 0
        self.data_specification.unit_column_number = 0
        self.data_specification.year_column_number = 0
        self.data_specification.value_column_number = 0
        self.rebuild_csv_rows()

    @property
    def header_is_included(self) -> bool:
        return self.data_specification.header_is_included

    @property
    def lines_to_skip(self) -> str:
        return self.data_specification.lines_to_skip

    @property
    def scenarios_to_ignore(self) -> str:
        """Return comma-separated scenario values"""
        return self.data_specification.scenarios_to_ignore

    @property
    def column_options(self) -> list[str]:
        return list(self.uploaded_data_preview_content[0])

    @property
    def scenario_column(self) -> str:
        column_number = self.data_specification.scenario_column_number
        return ([""] + self.column_options)[column_number]

    @scenario_column.setter
    def scenario_column(self, value):
        column_number = ([""] + self.column_options).index(value)
        self.data_specification.scenario_column_number = column_number

    @property
    def region_column(self) -> str:
        column_number = self.data_specification.region_column_number
        return ([""] + self.column_options)[column_number]

    @region_column.setter
    def region_column(self, value: str):
        column_number = ([""] + self.column_options).index(value)
        self.data_specification.region_column_number = column_number

    @property
    def variable_column(self) -> str:
        column_number = self.data_specification.variable_column_number
        return ([""] + self.column_options)[column_number]

    @variable_column.setter
    def variable_column(self, value: str):
        column_number = ([""] + self.column_options).index(value)
        self.data_specification.variable_column_number = column_number

    @property
    def item_column(self) -> str:
        column_number = self.data_specification.item_column_number
        return ([""] + self.column_options)[column_number]

    @item_column.setter
    def item_column(self, value: str):
        column_number = ([""] + self.column_options).index(value)
        self.data_specification.item_column_number = column_number

    @property
    def unit_column(self) -> str:
        column_number = self.data_specification.unit_column_number
        return ([""] + self.column_options)[column_number]

    @unit_column.setter
    def unit_column(self, value: str) -> None:
        column_number = ([""] + self.column_options).index(value)
        self.data_specification.unit_column_number = column_number

    @property
    def year_column(self) -> str:
        column_number = self.data_specification.year_column_number
        return ([""] + self.column_options)[column_number]

    @year_column.setter
    def year_column(self, value: str) -> None:
        column_number = ([""] + self.column_options).index(value)
        self.data_specification.year_column_number = column_number

    @property
    def value_column(self) -> str:
        column_number = self.data_specification.value_column_number
        return ([""] + self.column_options)[column_number]

    @value_column.setter
    def value_column(self, value: str) -> None:
        column_number = ([""] + self.column_options).index(value)
        self.data_specification.value_column_number = column_number

    @property
    def uploaded_data_preview_content(self) -> np.ndarray:
        if self.csv_rows is None:
            return np.array(["" for i in range(24)]).reshape((3, 8))

        # TODO: incorporate lines to ignore and scenarios to skip
        preview_table = []
        for row in self.csv_rows:
            if len(row) == self.most_frequent_ncolumn:
                preview_table.append(row)
            if len(preview_table) == 3:
                break
        if not self.header_is_included:
            assert self.most_frequent_ncolumn is not None
            header = ["Column " + str(i + 1) for i in range(self.most_frequent_ncolumn)]
            preview_table = [header] + preview_table[:2]
        else:
            preview_table[0] = [
                chr(colnum + 97) + ")  " + preview_table[0][colnum] for colnum in range(len(preview_table[0]))
            ]
        return np.array(preview_table)

    @property
    def output_data_preview_content(self) -> np.ndarray:
        uploaded_data_preview_content = self.uploaded_data_preview_content
        model_col = ["Model", self.model_name, self.model_name]
        scenario_colnum = self.data_specification.scenario_column_number
        if scenario_colnum == 0:
            scenario_col = ["Scenario", "", ""]
        else:
            scenario_col = ["Scenario"] + [uploaded_data_preview_content[i][scenario_colnum - 1] for i in (1, 2)]
        region_colnum = self.data_specification.region_column_number
        if region_colnum == 0:
            region_col = ["Region", "", ""]
        else:
            region_col = ["Region"] + [uploaded_data_preview_content[i][region_colnum - 1] for i in (1, 2)]
        variable_colnum = self.data_specification.variable_column_number
        if variable_colnum == 0:
            variable_col = ["Variable", "", ""]
        else:
            variable_col = ["Variable"] + [uploaded_data_preview_content[i][variable_colnum - 1] for i in (1, 2)]
        item_colnum = self.data_specification.item_column_number
        if item_colnum == 0:
            item_col = ["Item", "", ""]
        else:
            item_col = ["Item"] + [uploaded_data_preview_content[i][item_colnum - 1] for i in (1, 2)]
        unit_colnum = self.data_specification.unit_column_number
        if unit_colnum == 0:
            unit_col = ["Unit", "", ""]
        else:
            unit_col = ["Unit"] + [uploaded_data_preview_content[i][unit_colnum - 1] for i in (1, 2)]
        year_colnum = self.data_specification.year_column_number
        if year_colnum == 0:
            year_col = ["Year", "", ""]
        else:
            year_col = ["Year"] + [uploaded_data_preview_content[i][year_colnum - 1] for i in (1, 2)]
        value_colnum = self.data_specification.value_column_number
        if value_colnum == 0:
            value_col = ["Value", "", ""]
        else:
            value_col = ["Value"] + [uploaded_data_preview_content[i][value_colnum - 1] for i in (1, 2)]
        return np.array(
            [model_col, scenario_col, region_col, variable_col, item_col, unit_col, year_col, value_col]
        ).transpose()

    def intro(self, view: View, controller: Controller) -> None:  # type: ignore # noqa
        """Introduce MVC modules to each other"""
        self.view = view
        self.controller = controller

    def load_file(self, file_name: str) -> Optional[str]:
        """
        Load CSV file from the upload directory
        Returns None or an error message if an error is encountered
        """
        self.data_specification = DataSpecificationInput()
        assert len(file_name) > 0
        file_path = self.UPLOAD_DIR / Path(file_name)
        assert file_path.is_file()
        try:
            with open(str(file_path)) as csvfile:
                self.raw_csv_rows = csvfile.readlines()
                sample_data: str = "\n".join(self.raw_csv_rows[:1000])  # use X rows as sample data
                delimiters: str = "".join(Delimiter.get_models())
                format_sniffer = csv.Sniffer()
                csv_dialect = format_sniffer.sniff(sample_data, delimiters=delimiters)
                self.data_specification.delimiter = csv_dialect.delimiter
                self.data_specification.header_is_included = format_sniffer.has_header(sample_data)
                self.rebuild_csv_rows()
        except csv.Error:
            return "Could not determine delimiter when parsing file"
        except IOError:
            return "Errror when opening file"
        except:
            traceback.print_exc()
            return "Unexpected error when loading file"
        return None

    def remove_file(self, file_name: str) -> None:
        """Remove uploaded file from the upload directory"""
        assert len(file_name) > 0
        file_path = self.UPLOAD_DIR / Path(file_name)
        assert file_path.is_file()
        file_path.unlink()
