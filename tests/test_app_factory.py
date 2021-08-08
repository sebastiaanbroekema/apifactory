"""tests for app_factory module

currenlty tests:
alternative constructor methods
proper initialisation
"""
import os
from fastapi import FastAPI
from apifactory.app_factory import ApiFactory
from apifactory.database import Database

BASE_PATH = os.path.abspath(os.path.dirname(__file__))


def test_yaml():
    file_name = os.path.join(BASE_PATH, "testfiles/test.yaml")
    assert ApiFactory.from_yaml(file_name)


def test_json():
    file_name = os.path.join(BASE_PATH, "testfiles/test.json")
    assert ApiFactory.from_json(file_name)


def test_app_creation():
    file_name = os.path.join(BASE_PATH, "testfiles/test.yaml")
    app = ApiFactory.from_yaml(file_name).app_factory()
    assert isinstance(app, FastAPI)


def test_app_creation_customdb():
    class CustomClass(Database):
        ...

    file_name = os.path.join(BASE_PATH, "testfiles/test.yaml")
    app = ApiFactory.from_yaml(file_name, database=CustomClass)
    assert isinstance(app.db, CustomClass)
    # check if the final class is not of type DataBase
    assert not isinstance(type(app.db), Database)
    assert isinstance(app.app_factory(), FastAPI)
