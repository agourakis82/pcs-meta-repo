from pcs_toolbox.common import token_norm

def test_token_norm_basic():
    assert token_norm("Apple,") == "apple"
    assert token_norm("coördinate") == "coordinate"
    assert token_norm("NASA.") == "nasa"
    assert token_norm("") == ""
