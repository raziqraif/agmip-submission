import sys
import os
import pandas as pd
from pathlib import Path
import pytest
from typing import List

# Modify PATH so that the following imports work
sys.path.insert(0, os.path.dirname("scripts"))
from scripts.model import Model
from scripts.business import DataSpecification, DataCleaningService


"""
SAMPLE RAW CSV
[
    "Scenario,Region,Variable,Item,Year,Unit,Value",
    "SSP2_NoMt_NoCC_FlexA_DEV,CAN,CONS,RIC,2010,1000 t dm,162.6840595",
    "SSP2_NoMt_NoCC_FlexA_DEV,CAN,CONS,RIC,2020,1000 t dm,183.6566783",
    "SSP2_NoMt_NoCC_FlexA_DEV,CAN,CONS,RIC,2030,1000 t dm,170.3285805",
    "SSP2_NoMt_NoCC_FlexA_DEV,CAN,CONS,RIC,2050,1000 t dm,158.6103519",
    "SSP2_NoMt_NoCC_FlexA_WLD_2500,MEN,FEED,VFN|VEG,2050,1000 t fm,4661.274823",
    "SSP2_NoMt_NoCC_FlexA_WLD_2500,MEN,OTHU,VFN|VEG,2010,1000 t fm,120.3986869",
    "SSP2_NoMt_NoCC_FlexA_WLD_2500,MEN,OTHU,VFN|VEG,2020,1000 t fm,169.3291105",
    "SSP2_NoMt_NoCC_FlexA_WLD_2500,MEN,OTHU,VFN|VEG,2030,1000 t fm,151.8507839",
]

"""

TESTFILE_PATH = Model.UPLOAD_DIR / "temp_testfile.csv"


def create_test_file(input_data: List[str]) -> Path:
    """Create a test file from raw input data"""
    filepath = TESTFILE_PATH
    if filepath.exists():
        filepath.unlink()
    with open(str(filepath), "w+") as file:
        for row in input_data:
            file.write(row + "\n")
    return filepath


def print_test_file(filepath: Path) -> None:
    """Print the content of test file"""
    with open(str(filepath), "w+") as file:
        print(file.readlines())


@pytest.fixture
def data_specification() -> DataSpecification:
    """
    Return arguments required to initialize integrity checking states
    The arguments are based on SAMPLE_RAW_CSV
    """
    spec = DataSpecification()
    spec.delimiter = ","
    spec.header_is_included = False
    spec.initial_lines_to_skip = 0
    spec.scenarios_to_ignore = []
    spec.model_name = "AIM"
    spec.scenario_colnum = 1
    spec.region_colnum = 2
    spec.variable_colnum = 3
    spec.item_colnum = 4
    spec.unit_colnum = 6
    spec.year_colnum = 5
    spec.value_colnum = 7
    return spec


def test_duplicate_rows(data_specification: DataSpecification):
    """Test if duplicate rows are pruned correctly"""
    ROWS = [
        "SSP2_NoMt_NoCC_FlexA_WLD_2500,MEN,OTHU,VFN|VEG,2030,1000 t fm,151.8507839",  # NOSONAR
        "SSP2_NoMt_NoCC_FlexA_WLD_2500,MEN,OTHU,VFN|VEG,2030,1000 t fm,151.8507839",
        "SSP2_NoMt_NoCC_FlexA_WLD_2500,MEN,OTHU,VFN|VEG,2030,1000 t fm,151.8507839",
        "SSP2_NoMt_NoCC_FlexA_WLD_2500,MEN,OTHU,VFN|VEG,2030,1000 t fm,151.8507839",
    ]
    filepath = create_test_file(ROWS)
    data_specification.uploaded_filepath = filepath
    data_cleaner = DataCleaningService(data_specification)
    data_cleaner.parse_data()
    assert data_cleaner.nrows_duplicate == len(ROWS) - 1
    assert data_cleaner.nrows_accepted == 1


def test_rows_w_structural_issue(data_specification: DataSpecification):
    """Test if rows with field issues are pruned correctly"""
    ROWS = [
        "SSP2_NoMt_NoCC_FlexA_DEV,CAN,CONS,RIC,2010,1000 t dm,162.6840595",
        "SSP2_NoMt_NoCC_FlexA_DEV,CAN,CONS,RIC,2020,1000 t dm,183.6566783",  # NOSONAR
        "SSP2_NoMt_NoCC_FlexA_DEV,CAN,CONS,RIC,2030,1000 t dm,170.3285805",  # NOSONAR
        "SSP2_NoMt_NoCC_FlexA_DEV,CAN,CONS,RIC,2050,1000 t dm,158.6103519",  # NOSONAR
        "SSP2_NoMt_NoCC_FlexA_WLD_2500,MEN,FEED,VFN|VEG,2050,1000 t fm,4661.274823",  # NOSONAR
        "SSP2_NoMt_NoCC_FlexA_WLD_2500,MEN,OTHU,VFN|VEG,2010,1000 t fm,120.3986869",  # NOSONAR
        "SSP2_NoMt_NoCC_FlexA_WLD_2500,MEN,OTHU,VFN|VEG,2020,1000 t fm,169.3291105",  # NOSONAR
        "SSP2_NoMt_NoCC_FlexA_WLD_2500,MEN,OTHU,VFN|VEG,2030,1000 t fm,151.8507839",
        "row with mismatched ncols,a,a,a,a,a,a,a,a,a",
        "row with mismatched ncols",
        "row with mismatched ncols,,",
        "row with missing field 1,,,,,,",
        "row with missing field 2,,,,,,",
    ]
    filepath = create_test_file(ROWS)
    data_specification.uploaded_filepath = filepath
    data_cleaner = DataCleaningService(data_specification)
    data_cleaner.parse_data()
    assert data_cleaner.nrows_w_struct_issue == 5
    assert data_cleaner.nrows_accepted == len(ROWS) - 5


def test_rows_with_ignored_scenario(data_specification: DataSpecification):
    """Test if rows with an ignored scenario are pruned correctly"""
    ROWS = [
        "ignored scenario 1,CAN,CONS,RIC,2010,1000 t dm,162.6840595",
        "ignored scenario 2,CAN,CONS,RIC,2010,1000 t dm,162.6840595",
        "SSP2_NoMt_NoCC_FlexA_DEV,CAN,CONS,RIC,2020,1000 t dm,183.6566783",
        "SSP2_NoMt_NoCC_FlexA_DEV,CAN,CONS,RIC,2030,1000 t dm,170.3285805",
        "SSP2_NoMt_NoCC_FlexA_DEV,CAN,CONS,RIC,2050,1000 t dm,158.6103519",
        "SSP2_NoMt_NoCC_FlexA_WLD_2500,MEN,FEED,VFN|VEG,2050,1000 t fm,4661.274823",
        "SSP2_NoMt_NoCC_FlexA_WLD_2500,MEN,OTHU,VFN|VEG,2010,1000 t fm,120.3986869",
        "SSP2_NoMt_NoCC_FlexA_WLD_2500,MEN,OTHU,VFN|VEG,2020,1000 t fm,169.3291105",
        "SSP2_NoMt_NoCC_FlexA_WLD_2500,MEN,OTHU,VFN|VEG,2030,1000 t fm,151.8507839",
    ]
    ignored_scenarios = ["ignored scenario 1", "ignored scenario 2"]
    data_specification.scenarios_to_ignore = ignored_scenarios
    filepath = create_test_file(ROWS)
    data_specification.uploaded_filepath = filepath
    data_cleaner = DataCleaningService(data_specification)
    data_cleaner.parse_data()
    assert data_cleaner.nrows_w_ignored_scenario == len(ignored_scenarios)
    assert data_cleaner.nrows_accepted == len(ROWS) - len(ignored_scenarios)


def test_bad_labels(data_specification: DataSpecification) -> None:
    """Test if bad labels are identified correctly"""
    ROWS = [
        "ssp2_nomt_nocc_flexa_dev,Can,cons,ric,2020,1000 T dm,#DIV/0!",
        "SSP2_NoMt_NoCC_FlexA_DEV,World,CONS,RIC,2030,1000 t dm,NA",
    ]
    bad_labels = [
        "ssp2_nomt_nocc_flexa_dev",
        "Can",
        "cons",
        "ric",
        "1000 T dm",
        "#DIV/0!",
        "NA",
    ]
    fixed_labels = ["SSP2_NoMt_NoCC_FlexA_DEV", "CAN", "CONS", "RIC", "1000 t dm", "0", "0"]
    data_specification.uploaded_filepath = create_test_file(ROWS)
    data_cleaner = DataCleaningService(data_specification)
    data_cleaner.parse_data()
    print(data_cleaner.bad_labels_table)
    for label in bad_labels:
        print(label)
        assert data_cleaner.bad_labels_table[data_cleaner.bad_labels_table["Label"] == label].shape[0] != 0
    for label in fixed_labels:
        print(label)
        assert data_cleaner.bad_labels_table[data_cleaner.bad_labels_table["Fix"] == label].shape[0] != 0
