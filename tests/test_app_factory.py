"""tests for app_factory module

currenlty only tests alternative constructor methods
"""
import os
from apifactory.app_factory import ApiFactory


BASE_PATH = os.path.abspath(os.path.dirname(__file__))


def test_yaml():
    file_name = os.path.join(BASE_PATH, "testfiles/test.yaml")
    assert ApiFactory.from_yaml(file_name)


def test_json():
    file_name = os.path.join(BASE_PATH, "testfiles/test.json")
    assert ApiFactory.from_json(file_name)
