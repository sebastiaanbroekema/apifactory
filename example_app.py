import os
from apifactory.app_factory import ApiFactory


BASE_PATH = os.path.abspath(os.path.dirname(__file__))

file_name = os.path.join(BASE_PATH, "tests/testfiles/test.yaml")
app = ApiFactory.from_yaml(file_name).app_factory()
