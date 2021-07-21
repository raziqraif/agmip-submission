import math

from scripts.dataaccess import RuleGateway


def test_fix_queries():
    assert RuleGateway.query_fix_from_value_fix_table("NA") == "0"
    assert RuleGateway.query_fix_from_value_fix_table("na") == "0"
    assert RuleGateway.query_fix_from_value_fix_table("#DIV/0!") == "0"
    assert RuleGateway.query_fix_from_region_fix_table("World") == "WLD"
    assert RuleGateway.query_fix_from_region_fix_table("world") == "WLD"


def test_matching_queries():
    assert RuleGateway.query_matching_scenario("ssp2_nomt_nocc_FLEXA_DEV") == "SSP2_NoMt_NoCC_FlexA_DEV"
    assert RuleGateway.query_matching_region("Wld") == "WLD"
    # Matching queries should not return result from the fix table
    assert RuleGateway.query_matching_region("world") != "WLD"
    assert RuleGateway.query_matching_variable("Cons") == "CONS"
    assert RuleGateway.query_matching_variable("oTHU") == "OTHU"
    assert RuleGateway.query_matching_item("Vfn|Veg") == "VFN|VEG"
    assert RuleGateway.query_matching_unit("1000 T dm") == "1000 t dm"


def test_partially_matching_queries():
    scenarios = RuleGateway._scenarios
    assert RuleGateway.query_partially_matching_scenario("dummy_label") in scenarios
    variables = RuleGateway._variables
    assert RuleGateway.query_partially_matching_variable("dummy_label") in variables
    items = RuleGateway._items
    assert RuleGateway.query_partially_matching_item("dummy_label") in items
    regions = RuleGateway._regions
    assert RuleGateway.query_partially_matching_region("dummy_label") in regions
    units = RuleGateway._units
    assert RuleGateway.query_partially_matching_unit("dummy_label") in units


def test_minimum_and_maximum_variable_value():
    assert RuleGateway.query_variable_min_value("POPT", "million") > -1
    assert RuleGateway.query_variable_max_value("POPT", "million") > 1000
    assert RuleGateway.query_variable_min_value("ECH4", "MtCO2e") >= 0
    assert RuleGateway.query_variable_max_value("ECH4", "MtCO2e") <= math.inf
    assert RuleGateway.query_variable_min_value("YILD", "dm t/ha") >= 0
    assert RuleGateway.query_variable_max_value("YILD", "fm t/ha") <= 1000