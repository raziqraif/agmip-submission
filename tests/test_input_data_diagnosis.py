import sys
import os
import pandas as pd
from pathlib import Path
import pytest
from typing import List

# Modify PATH so that the following imports work
sys.path.insert(0, os.path.dirname("scripts"))
from scripts.model import Model
from scripts.domain import InputDataDiagnosis, InputDataEntity, OutputDataEntity


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

TESTFILE_PATH = Model.UPLOADDIR_PATH / "temp_testfile.csv"


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


def populate_input_entity_based_on_sample_raw_csv(input_entity: InputDataEntity) -> None:
    """ Populate input entity """
    input_entity.delimiter = ","
    input_entity.header_is_included = False
    input_entity.initial_lines_to_skip = 0
    input_entity.scenarios_to_ignore = []
    input_entity.model_name = "AIM"
    input_entity.scenario_colnum = 1
    input_entity.region_colnum = 2
    input_entity.variable_colnum = 3
    input_entity.item_colnum = 4
    input_entity.unit_colnum = 6
    input_entity.year_colnum = 5
    input_entity.value_colnum = 7


def test_explore():
    """Test if duplicate rows are pruned correctly"""
    ROWS = [
        "SSP2_NoMt_NoCC_FlexA_WLD_2500,mEN,oTHU,VfN|VEG,2030,1000 t fm,151.8507839",  # NOSONAR
    ]
    filepath = create_test_file(ROWS)
    input_entity = InputDataEntity.create(filepath)
    populate_input_entity_based_on_sample_raw_csv(input_entity)
    diagnosis = InputDataDiagnosis.create(input_entity)
    assert diagnosis.nrows_duplicate == len(ROWS) - 1
    assert diagnosis.nrows_accepted == 1


def test_duplicate_rows():
    """Test if duplicate rows are pruned correctly"""
    ROWS = [
        "SSP2_NoMt_NoCC_FlexA_WLD_2500,MEN,OTHU,VFN|VEG,2030,1000 t fm,151.8507839",  # NOSONAR
        "SSP2_NoMt_NoCC_FlexA_WLD_2500,MEN,OTHU,VFN|VEG,2030,1000 t fm,151.8507839",
        "SSP2_NoMt_NoCC_FlexA_WLD_2500,MEN,OTHU,VFN|VEG,2030,1000 t fm,151.8507839",
        "SSP2_NoMt_NoCC_FlexA_WLD_2500,MEN,OTHU,VFN|VEG,2030,1000 t fm,151.8507839",
    ]
    filepath = create_test_file(ROWS)
    input_entity = InputDataEntity.create(filepath)
    populate_input_entity_based_on_sample_raw_csv(input_entity)
    diagnosis = InputDataDiagnosis.create(input_entity)
    assert diagnosis.nrows_duplicate == len(ROWS) - 1
    assert diagnosis.nrows_accepted == 1


def test_rows_w_structural_issue():
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
    input_entity = InputDataEntity.create(filepath)
    populate_input_entity_based_on_sample_raw_csv(input_entity)
    diagnosis = InputDataDiagnosis.create(input_entity)
    assert diagnosis.nrows_w_struct_issue == 5
    assert diagnosis.nrows_accepted == len(ROWS) - 5


def test_rows_with_ignored_scenario():
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
    filepath = create_test_file(ROWS)
    input_entity = InputDataEntity.create(filepath)
    populate_input_entity_based_on_sample_raw_csv(input_entity)
    input_entity.scenarios_to_ignore = ignored_scenarios
    diagnosis = InputDataDiagnosis.create(input_entity)
    assert diagnosis.nrows_w_ignored_scenario == len(ignored_scenarios)
    assert diagnosis.nrows_accepted == len(ROWS) - len(ignored_scenarios)


def test_bad_labels() -> None:
    """Test if bad labels are identified correctly"""
    ROWS = [
        "ssp2_nomt_nocc_flexa_dev,Can,cons,ric,2020,1000 T dm,#DIV/0!",
        "SSP2_NoMt_NoCC_FlexA_DEV,World,CONS,RIC,2030,1000 t dm,NA",
    ]
    bad_labels = ["ssp2_nomt_nocc_flexa_dev", "Can", "cons", "ric", "1000 T dm", "#DIV/0!", "NA", "World"]
    fixed_labels = ["SSP2_NoMt_NoCC_FlexA_DEV", "CAN", "CONS", "RIC", "1000 t dm", "0", "0", "WLD"]
    input_entity = InputDataEntity.create(create_test_file(ROWS))
    populate_input_entity_based_on_sample_raw_csv(input_entity)
    diagnosis = InputDataDiagnosis.create(input_entity)
    print(diagnosis.bad_labels)
    for label in bad_labels:
        print(label)
    for label in fixed_labels:
        print(label)
    # TODO: do more fine-grained assertions
    assert len(diagnosis.bad_labels) == len(bad_labels)


def test_unknown_labels() -> None:
    """Test if unknown labels are identified correctly"""
    ROWS = ["SSP2_NoMt_NoCC_FlexA_XYZW,MYXW,YIELDX,RICEX,2010,1000 pxyz dm,162.6840595"]
    unknown_labels = [
        "SSP2_NoMt_NoCC_FlexA_XYZW",
        "MYXW",
        "YIELDX",
        "RICEX",
        "1000 pxyz dm",
    ]
    input_entity = InputDataEntity.create(create_test_file(ROWS))
    populate_input_entity_based_on_sample_raw_csv(input_entity)
    diagnosis = InputDataDiagnosis.create(input_entity)
    print(diagnosis.bad_labels)
    assert len(diagnosis.unknown_labels) == len(unknown_labels)
