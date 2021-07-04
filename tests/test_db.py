"""module for testing Database class
"""
from apifactory.database import Database


def test_db_table_inclusion():
    db = Database("sqlite:///tests/testdb/test.db")
    assert hasattr(db.models, "Users")
    assert hasattr(db.models, "Persons")
    assert hasattr(db.models, "test_table")
