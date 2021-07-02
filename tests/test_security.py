"""tests for checking various functionalities from the security module
"""
from apifactory.security import Hash


def test_hash():
    hash_ = Hash()
    encrypted = hash_.bcrypt("bla")
    assert hash_.verify("bla", encrypted) is True
