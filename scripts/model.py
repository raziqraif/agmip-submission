from __future__ import annotations  # Delay the evaluation of undefined types
import os
from pathlib import Path
from typing import Any, Optional, Union

import csv
import numpy as np
import pandas as pd

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
        self.model_name: Optional[str] = None
        self.delimiter: Optional[str] = None
        self.header_is_included: Optional[bool] = None
        self.lines_to_skip: Optional[str] = None
        self.scenarios_to_ignore: Optional[str] = None
        self.scenario_column: Optional[str] = None
        self.region_column: Optional[str] = None
        self.variable_column: Optional[str] = None
        self.item_column: Optional[str] = None
        self.unit_column: Optional[str] = None
        self.year_column: Optional[str] = None
        self.value_column: Optional[str] = None


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
        self.entered_data_specification: DataSpecificationInput = DataSpecificationInput()
        self.guessed_data_specification: DataSpecificationInput = DataSpecificationInput()
        self.dataframe = None

        self.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

    @property
    def model_names(self) -> list[str]:
        return ["Model 1", "Model 2", "Model 3"]

    @property
    def model_name(self) -> str:
        return "Model 3"

    @property
    def delimiter(self) -> str:
        return Delimiter.COMMA

    @property
    def header_is_included(self) -> bool:
        return True

    @property
    def lines_to_skip(self) -> str:
        return "0"

    @property
    def scenarios_to_ignore(self) -> str:
        """Return comma-separated scenario values"""
        return ""

    @property
    def column_options(self) -> list[str]:
        return ["Column " + str(i) for i in range(1, 9)]

    @property 
    def scenario_column(self) -> str:
        return "Column 1"

    @property
    def region_column(self) -> str:
        return "Column 2"

    @property
    def variable_column(self) -> str:
        return "Column 3"
    
    @property
    def item_column(self) -> str:
        return "Column 4"
    
    @property
    def unit_column(self) -> str:
        return "Column 5"
    
    @property
    def year_column(self) -> str:
        return "Column 6"
    
    @property
    def value_column(self) -> str:
        return "Column 7"

    @property
    def uploaded_data_preview_content(self) -> np.ndarray:
        return np.array(["Upload" for i in range(24)]).reshape((3,8))

    @property
    def output_data_preview_content(self) -> np.ndarray:
        return np.array(["Output" for i in range(24)]).reshape((3,8))

    def intro(self, view: View, controller: Controller) -> None:  # type: ignore # noqa
        """Introduce MVC modules to each other"""
        self.view = view
        self.controller = controller

    def load_file(self, file_name: str) -> Optional[str]:
        """
        Load CSV file from the upload directory
        Returns None or an error message if an error is encountered
        """
        assert len(file_name) > 0
        file_path = self.UPLOAD_DIR / Path(file_name)
        assert file_path.is_file()
        try:
            with open(str(file_path)) as csvfile:
                format_sniffer = csv.Sniffer()
                sample_data = csvfile.read(100000)  # Create a sample data of up to ~100kB
                csvfile.seek(0)  # Reset the file pointer
                csv_dialect = format_sniffer.sniff(sample_data)  
                self.guessed_data_specification.header_is_included = format_sniffer.has_header(sample_data)

                reader = csv.reader(csvfile, csv_dialect)
                rows = [row for row in reader]
                number_of_columns_list = np.array([len(row) for row in rows])
                most_frequent_number_of_columns = np.bincount(number_of_columns_list).argmax()
                # Prepare data
        except csv.Error:
            return "Could not determine delimiter when parsing file"
        except IOError:
            return "Errror when opening file"
        except:
            return "Unexpected error when loading file"
        return None

    def remove_file(self, file_name: str) -> None:
        """Remove uploaded file from the upload directory"""
        assert len(file_name) > 0
        file_path = self.UPLOAD_DIR / Path(file_name)
        assert file_path.is_file()
        file_path.unlink()
