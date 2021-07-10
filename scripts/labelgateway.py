import difflib
from pathlib import Path
from typing import Dict, Set, Optional
from numpy import diff

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
    # Fix tables
    __region_fix_table: DataFrame = __spreadsheet["RegionFixTable"]
    # - query for value fix table needs to be fast, so we store the table in a dictionary. The
    # - "value" field becomes a dict key and the "fix" field becomes a dict value
    # @date July 9 2021
    __value_fix_table: Dict[str, str] = dict(__spreadsheet["ValueFixTable"].iloc[:, 1:].values)
    for key in __value_fix_table.keys():
        __value_fix_table[key] = str(__value_fix_table[key])
    # Valid columns
    _model_names = set(__model_table["Model"].astype("str"))
    _scenarios = set(__scenario_table["Scenario"].astype("str"))
    _regions = set(__region_table["Region"].astype("str"))
    _variables = set(__variable_table["Variable"].astype("str"))
    _items = set(__item_table["Item"].astype("str"))
    _units = set(__unit_table["Unit"].astype("str"))
    _years = set(__year_table["Year"].astype("str"))

    @classmethod
    def query_model_names(cls) -> Set[str]:
        return cls._model_names

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
        table = cls.__scenario_table
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
        table = cls.__region_table
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
        table = cls.__variable_table
        table = table[table["Variable"].str.lower() == variable]
        assert table.shape[0] <= 1
        if table.shape[0] != 0:
            return str(table.iloc[0]["Variable"])  # type: ignore
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
        table = cls.__item_table
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
        table = cls.__unit_table
        table = table[table["Unit"].str.lower() == unit]
        assert table.shape[0] <= 1
        if table.shape[0] != 0:
            return str(table.iloc[0]["Unit"])  # type: ignore
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
        fix_table = cls.__value_fix_table
        try:
            return fix_table[value.lower()]
        except:
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
        """Returns the min value"""
        return 0.0

    @classmethod
    def query_variable_max_value(cls, variable: str) -> Optional[float]:
        return 1000000.0
