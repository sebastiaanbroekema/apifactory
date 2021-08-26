"""unit tests for utils
"""
import pytest
from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, Integer


from apifactory.utils import PrimaryKeyAmountError, primary_key_checker


def test_primarykeyerror():
    with pytest.raises(PrimaryKeyAmountError):
        raise PrimaryKeyAmountError
    assert str(PrimaryKeyAmountError)


def test_primary_key_checker():
    base = declarative_base()

    class Failure(base):
        id = Column(Integer, primary_key=True)
        id2 = Column(Integer, primary_key=True)
        __tablename__ = "failure"

    with pytest.raises(PrimaryKeyAmountError):
        primary_key_checker(Failure)
