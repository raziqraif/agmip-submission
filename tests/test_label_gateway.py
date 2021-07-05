from scripts.labelgateway import LabelGateway


def test_fix_queries():
    assert LabelGateway.query_fix_from_value_fix_table("NA") == "0"
    assert LabelGateway.query_fix_from_value_fix_table("na") == "0"
    assert LabelGateway.query_fix_from_region_fix_table("World") == "WLD"
    assert LabelGateway.query_fix_from_region_fix_table("world") == "WLD"


def test_matching_queries():
    assert LabelGateway.query_matching_scenario("ssp2_nomt_nocc_FLEXA_DEV") == "SSP2_NoMt_NoCC_FlexA_DEV"
