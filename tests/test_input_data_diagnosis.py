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


class InputEntityFactory:

    TESTFILE_PATH = Model.UPLOADDIR_PATH / "temp_testfile.csv"

    @classmethod
    def create_from_sample_rows(cls, rows: List[str]) -> InputDataEntity:
        """
        Create and return an input entity
        The format of the argument (like its column arrangement or delimiter) must be like in the following example

        sample_rows = [
            "Scenario,Region,Variable,Item,Year,Unit,Value",
            "SSP2_NoMt_NoCC_FlexA_DEV,CAN,CONS,RIC,2020,1000 t dm,183.6566783",
            "SSP2_NoMt_NoCC_FlexA_WLD_2500,MEN,OTHU,VFN|VEG,2030,1000 t fm,151.8507839",
        ]
        """
        filepath = cls._create_test_file(rows)
        input_entity = InputDataEntity.create(filepath)
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
        return input_entity

    @classmethod
    def _create_test_file(cls, input_data: List[str]) -> Path:
        """Create a test file from raw input data"""
        filepath = cls.TESTFILE_PATH
        if filepath.exists():
            filepath.unlink()
        with open(str(filepath), "w+") as file:
            for row in input_data:
                file.write(row + "\n")
        return filepath


def test_explore():
    """Test if duplicate rows are pruned correctly"""
    ROWS = [
        "SSP2_NoMt_NoCC_FlexA_WLD_2500,mEN,oTHU,VfN|VEG,2030,1000 t fm,151.8507839",  # NOSONAR
    ]
    input_entity = InputEntityFactory.create_from_sample_rows(ROWS)
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
    input_entity = InputEntityFactory.create_from_sample_rows(ROWS)
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
        "SSP2_NoMt_NoCC_FlexA_WLD_2500,MEN,OTHU,VFN|VEG,2030,1000 t fm,99999999999999999999",
        "row with mismatched ncols,a,a,a,a,a,a,a,a,a",
        "row with mismatched ncols",
        "row with mismatched ncols,,",
        "row with missing field 1,,,,,,",
        "row with missing field 2,,,,,,",
    ]
    input_entity = InputEntityFactory.create_from_sample_rows(ROWS)
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
    input_entity = InputEntityFactory.create_from_sample_rows(ROWS)
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
    input_entity = InputEntityFactory.create_from_sample_rows(ROWS)
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
    input_entity = InputEntityFactory.create_from_sample_rows(ROWS)
    diagnosis = InputDataDiagnosis.create(input_entity)
    print(diagnosis.bad_labels)
    assert len(diagnosis.unknown_labels) == len(unknown_labels)


def test_fixed_unknown_label_w_out_of_bound_value() -> None:
    """
    Test if records with unknown labels and out-of-bound values are identified correctly
    (after the labels were fixed)
    """
    ROWS = [
        "SSP2_NoMt_NoCC_FlexA_WLD_2500,MEN,POPT_XYZW,VFN|VEG,2030,million,151",  # valid value
        "SSP2_NoMt_NoCC_FlexA_WLD_2500,MEN,POPT_XYZW,VFN|VEG,2030,million,99999999999999999999",  # invalid value
        "SSP2_NoMt_NoCC_FlexA_WLD_2500,MEN,POPT,VFN|VEG,2030,million_XYZW,99999999999999999999",  # invalid value
    ]
    input_entity = InputEntityFactory.create_from_sample_rows(ROWS)
    diagnosis = InputDataDiagnosis.create(input_entity)
    assert len(diagnosis.unknown_labels) == 2
    for label_info in diagnosis.unknown_labels:
        if label_info.associated_column == diagnosis.VARIABLE_COLNAME:
            label_info.fix = "POPT"
        elif label_info.associated_column == diagnosis.UNIT_COLNAME:
            label_info.fix = "million"
        else:
            print(label_info)
            raise Exception("Unexpected unknown label info")
    output_entity = OutputDataEntity.create(input_entity, diagnosis)
    assert output_entity.processed_data.shape[0] == len(ROWS)
    assert diagnosis.rediagnose_n_filter_output_data(output_entity) == True
    with open(diagnosis.FILTERED_OUTPUT_DSTPATH, "r") as filteredfile:
        lines = filteredfile.readlines()
        assert len(lines) == 1  # filtered output file should contain only 1 valid row
        assert lines[0].strip('\n').split(",")[-1] == '151'