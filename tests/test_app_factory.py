"""tests for app_factory module

currenlty tests:
alternative constructor methods
proper initialisation
"""
import os
from fastapi import FastAPI
from apifactory.app_factory import ApiFactory


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
