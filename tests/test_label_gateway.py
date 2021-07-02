from scripts.labelgateway import LabelGateway


def test_fix_value():
	assert LabelGateway.get_fixed_value("NA") == '0'