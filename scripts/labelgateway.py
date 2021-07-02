from pathlib import Path
from typing import Dict, Set

import pandas as pd
from pandas import DataFrame


WORKING_DIR: Path = Path(__name__).parent.parent / "workingdir"  # <PROJECT_DIR>/workingdir
VALID_LABELS_SPREADSHEET: Path = WORKING_DIR / "label_data.xlsx"


class LabelGateway:
    """
    Provides a gateway to label-related data
    Intended design pattern = https://martinfowler.com/eaaCatalog/gateway.html
    """

    # Spreadsheet containing labels information
    __spreadsheet: Dict[str, DataFrame] = pd.read_excel(
        str(VALID_LABELS_SPREADSHEET),
        engine="openpyxl",
        sheet_name=None,
        keep_default_na=False,
    )
    # Valid labels table
    __model_table: DataFrame = __spreadsheet["ModelTable"]
    __scenario_table: DataFrame = __spreadsheet["ScenarioTable"]
    __region_table: DataFrame = __spreadsheet["RegionTable"]
    __variable_table: DataFrame = __spreadsheet["VariableTable"]
    __item_table: DataFrame = __spreadsheet["ItemTable"]
    __unit_table: DataFrame = __spreadsheet["UnitTable"]
    __year_table: DataFrame = __spreadsheet["YearTable"]
    # Swap table
    __region_fix_table: DataFrame = __spreadsheet["RegionFixTable"]
    __value_fix_table: DataFrame = __spreadsheet["ValueFixTable"]
    # Valid columns
    valid_model_names: Set[str] = set(__model_table["Model"])
    valid_scenarios: Set[str] = set(__scenario_table["Scenario"])
    valid_regions: Set[str] = set(__region_table["Region"])
    valid_variables: Set[str] = set(__variable_table["Variable"])
    valid_items: Set[str] = set(__item_table["Item"])
    valid_units: Set[str] = set(__unit_table["Unit"])
    valid_years: Set[str] = set(__year_table["Year"])

    @classmethod
    def get_fixed_value(cls, value: str) -> str:
        """
        Checks if value can be fixed and returns the fix
        Returns the value back if the it does not need fixing or cannot be fixed
        """
        dataframe = cls.__value_fix_table
        # Get all rows containing the fix
        dataframe = dataframe[dataframe["Value"] == value.lower()]
        assert dataframe.shape[0] <= 1
        # No fixes are found
        if dataframe.shape[0] == 0:
            return value
        return dataframe["Fix"].loc(0)
