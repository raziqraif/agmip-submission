import pytest

from scripts import model as scsa_model
from scripts import view as scsa_view
from scripts import controller as scsa_controller

# Create MVC objects
model = scsa_model.Model()

RAW_CSV = [
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

IGNORED_SCENARIO_ROWS = [
    "IGNORED_SCENARIO_1,MEN,FEED,VFN|VEG,2050,1000 t fm,4661.274823",
    "IGNORED_SCENARIO_2,MEN,FEED,VFN|VEG,2050,1000 t fm,4661.274823",
]

scenarios_to_ignore = ["IGNORED_SCENARIO_1", "IGNORED_SCENARIO_2"]


@pytest.fixture
def init_states_kwargs() -> dict:
    return {
        'raw_csv':[],
        'delimiter':',',
        'header_is_included':False,
        'lines_to_skip':0,
        'scenarios_to_ignore':[],
        'model_name':"AIM",
        'scenario_colnum':1,
        'region_colnum':2,
        'variable_colnum':3,
        'item_colnum':4,
        'unit_colnum':5,
        'year_colnum':6,
        'value_colnum':7,
    }


def test_duplicate_rows(init_states_kwargs: dict):
    DUPLICATE_ROWS = [
        "SSP2_NoMt_NoCC_FlexA_WLD_2500,MEN,OTHU,VFN|VEG,2030,1000 t fm,151.8507839",
        "SSP2_NoMt_NoCC_FlexA_WLD_2500,MEN,OTHU,VFN|VEG,2030,1000 t fm,151.8507839",
        "SSP2_NoMt_NoCC_FlexA_WLD_2500,MEN,OTHU,VFN|VEG,2030,1000 t fm,151.8507839",
        "SSP2_NoMt_NoCC_FlexA_WLD_2500,MEN,OTHU,VFN|VEG,2030,1000 t fm,151.8507839",
    ]
    init_states_kwargs['raw_csv'] = DUPLICATE_ROWS
    model = scsa_model.Model()
    model.init_integrity_checking_states(**init_states_kwargs)
    assert len(model.duplicate_rows) == len(DUPLICATE_ROWS) - 1

