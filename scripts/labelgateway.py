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
    __model_table: DataFrame = __spreadsheet["ModelTable"]
    __scenario_table: DataFrame = __spreadsheet["ScenarioTable"]
    __region_table: DataFrame = __spreadsheet["RegionTable"]
    __variable_table: DataFrame = __spreadsheet["VariableTable"]
    __item_table: DataFrame = __spreadsheet["ItemTable"]
    __unit_table: DataFrame = __spreadsheet["UnitTable"]
    __year_table: DataFrame = __spreadsheet["YearTable"]
    # Fix table
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
    def query_matching_scenario(cls, scenario: str) -> Optional[str]:
        """Returns a matching value (ignoring case), or None"""
        scenario = scenario.lower()
        table = cls.__scenario_table
        table = table[table["Scenario"].str.lower() == scenario]
        assert table.shape[0] <= 1
        if table.shape[0] != 0:
            return str(table.iloc[0]["Scenario"])  # type: ignore
        return None
    
    @classmethod
    def query_matching_region(cls, region: str) -> Optional[str]:
        """Returns a matching value (ignoring case), or None"""
        region= region.lower()
        table = cls.__scenario_table
        table = table[table["Region"].str.lower() == region]
        assert table.shape[0] <= 1
        if table.shape[0] != 0:
            return str(table.iloc[0]["Region"])  # type: ignore
        return None
    
    @classmethod
    def query_matching_variable(cls, variable: str) -> Optional[str]:
        """Returns a matching value (ignoring case), or None"""
        variable= variable.lower()
        table = cls.__scenario_table
        table = table[table["Variable"].str.lower() == variable]
        assert table.shape[0] <= 1
        if table.shape[0] != 0:
            return str(table.iloc[0]["Variable"])  # type: ignore
        return None

    @classmethod
    def query_matching_item(cls, item: str) -> Optional[str]:
        """Returns a matching value (ignoring case), or None"""
        item= item.lower()
        table = cls.__scenario_table
        table = table[table["Item"].str.lower() == item]
        assert table.shape[0] <= 1
        if table.shape[0] != 0:
            return str(table.iloc[0]["Item"])  # type: ignore
        return None

    @classmethod
    def query_matching_unit(cls, unit: str) -> Optional[str]:
        """Returns a matching value (ignoring case), or None"""
        unit= unit.lower()
        table = cls.__scenario_table
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
    def query_fix_from_region_fix_table(cls, region: str) -> str:
        """Checks if a fix exists in the fix table and returns it. Returns None otherwise."""
        fix_table = cls.__region_fix_table
        # Get all rows containing the fix
        fix_table = fix_table[fix_table["Region"] == region.lower()]
        assert fix_table.shape[0] <= 1
        # Fix was found
        if fix_table.shape[0] != 0:
            return str(fix_table.iloc[0]["Fix"])
        return None
