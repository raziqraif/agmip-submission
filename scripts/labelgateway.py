from pathlib import Path
from typing import Dict, Set, Optional

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
    __model_table = __spreadsheet["ModelTable"]
    __scenario_table = __spreadsheet["ScenarioTable"]
    __region_table = __spreadsheet["RegionTable"]
    __variable_table = __spreadsheet["VariableTable"]
    __item_table = __spreadsheet["ItemTable"]
    __unit_table = __spreadsheet["UnitTable"]
    __year_table = __spreadsheet["YearTable"]
    # Fix table
    __region_fix_table: DataFrame = __spreadsheet["RegionFixTable"]
    __value_fix_table: DataFrame = __spreadsheet["ValueFixTable"]
    # Valid columns
    __model_names = set(__model_table["Model"])
    __scenarios = set(__scenario_table["Scenario"])
    __regions = set(__region_table["Region"])
    __variables = set(__variable_table["Variable"])
    __items = set(__item_table["Item"])
    __units = set(__unit_table["Unit"])
    __years = set(__year_table["Year"])

    @classmethod
    def query_model_names(cls) -> Set[str]:
        return cls.__model_names

    @classmethod
    def query_label_in_model_names(cls, label: str) -> bool:
        return label in cls.__model_names

    @classmethod
    def query_label_in_scenarios(cls, label: str) -> bool:
        return label in cls.__scenarios

    @classmethod
    def query_label_in_regions(cls, label: str) -> bool:
        return label in cls.__regions

    @classmethod
    def query_label_in_variables(cls, label: str) -> bool:
        return label in cls.__variables
    
    @classmethod
    def query_label_in_items(cls, label: str) -> bool:
        return label in cls.__items

    @classmethod
    def query_label_in_units(cls, label: str) -> bool:
        return label in cls.__units

    @classmethod
    def query_label_in_years(cls, label: str) -> bool:
        return label in cls.__years

    @classmethod
    def query_matching_scenario(cls, scenario: str) -> Optional[str]:
        """Returns a matching scenario (ignoring case), or None"""
        scenario = scenario.lower()
        table = cls.__scenario_table
        table = table[table["Scenario"].str.lower() == scenario]
        assert table.shape[0] <= 1
        if table.shape[0] != 0:
            return str(table.iloc[0]["Scenario"])  # type: ignore
        return None
    
    @classmethod
    def query_matching_region(cls, region: str) -> Optional[str]:
        """Returns a matching region (ignoring case), or None"""
        region= region.lower()
        table = cls.__region_table
        table = table[table["Region"].str.lower() == region]
        assert table.shape[0] <= 1
        if table.shape[0] != 0:
            return str(table.iloc[0]["Region"])  # type: ignore
        return None
    
    @classmethod
    def query_matching_variable(cls, variable: str) -> Optional[str]:
        """Returns a matching variable (ignoring case), or None"""
        variable= variable.lower()
        table = cls.__variable_table
        table = table[table["Variable"].str.lower() == variable]
        assert table.shape[0] <= 1
        if table.shape[0] != 0:
            return str(table.iloc[0]["Variable"])  # type: ignore
        return None

    @classmethod
    def query_matching_item(cls, item: str) -> Optional[str]:
        """Returns a matching item (ignoring case), or None"""
        item= item.lower()
        table = cls.__item_table
        table = table[table["Item"].str.lower() == item]
        assert table.shape[0] <= 1
        if table.shape[0] != 0:
            return str(table.iloc[0]["Item"])  # type: ignore
        return None

    @classmethod
    def query_matching_unit(cls, unit: str) -> Optional[str]:
        """Returns a matching unit (ignoring case), or None"""
        unit= unit.lower()
        table = cls.__unit_table
        table = table[table["Unit"].str.lower() == unit]
        assert table.shape[0] <= 1
        if table.shape[0] != 0:
            return str(table.iloc[0]["Unit"])  # type: ignore
        return None

    @classmethod
    def query_fix_from_value_fix_table(cls, value: str) -> Optional[str]:
        """Checks if a fix exists in the fix table and returns it. Returns None otherwise."""
        fix_table = cls.__value_fix_table
        # Get all rows containing the fix
        fix_table = fix_table[fix_table["Value"] == value.lower()]
        assert fix_table.shape[0] <= 1
        # Fix was found
        if fix_table.shape[0] != 0:
            return str(fix_table.iloc[0]["Fix"])
        return None

    @classmethod
    def query_fix_from_region_fix_table(cls, region: str) -> Optional[str]:
        """Checks if a fix exists in the fix table and returns it. Returns None otherwise."""
        fix_table = cls.__region_fix_table
        # Get all rows containing the fix
        fix_table = fix_table[fix_table["Region"] == region.lower()]
        assert fix_table.shape[0] <= 1
        # Fix was found
        if fix_table.shape[0] != 0:
            return str(fix_table.iloc[0]["Fix"])
        return None

    @classmethod
    def query_variable_min_value(cls, variable: str) -> Optional[float]:
        return 0.0
    
    @classmethod
    def query_variable_max_value(cls, variable: str) -> Optional[float]:
        return 0.0