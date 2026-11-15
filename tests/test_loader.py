from src.data.loader import canonical,decode_until_stable,digest


def test_recursive_decoding_and_canonicalization():
    assert decode_until_stable("%2527") == "'"
    assert canonical(" A%20%20B ")=="a b"
    assert digest("x")==digest("x")
