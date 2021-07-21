import difflib
import math
import numpy as np
from numpy import diff, mat
from pathlib import Path
from typing import Dict, List, Set, Optional, Tuple

import pandas as pd
from pandas import DataFrame


WORKING_DIR: Path = Path(__name__).parent.parent / "workingdir"  # <PROJECT_DIR>/workingdir
VALID_LABELS_SPREADSHEET: Path = WORKING_DIR / "RuleTables.xlsx"


class RuleGateway:
    """
    Provides a gateway to the spreadsheet that contains rules about accepted field values, automatic fix, etc
    Intended pattern = https://martinfowler.com/eaaCatalog/gateway.html
    """

    # Spreadsheet containing labels information
    __spreadsheet: Dict[str, DataFrame] = pd.read_excel(
        str(VALID_LABELS_SPREADSHEET),
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
