"""for generating an entire app
"""

from json import load as jsonload
from yaml import load, Loader
from fastapi import FastAPI

from apifactory.route_factory import Routers
from apifactory.security import Security
from apifactory.utils import add_routes
from apifactory.database import Database
from apifactory.schemas import Schemas


class ApiFactory:
    """[summary]"""

    def __init__(self, database_url, usermodel_name, jwt_key, config):
        self.db = Database(database_url)
        self.schemas = Schemas(self.db.models)
        usermodel = getattr(self.db.models, usermodel_name)
        userschema = getattr(self.schemas, usermodel_name)
        self.security = Security(usermodel, self.db.get_db, jwt_key)
        self.routers = Routers(
            self.db.models,
            self.schemas,
            config,
            self.db.get_db,
            self.security.get_current_user,
            userschema,
        )

    def app_factory(self):
        """[summary]

        Returns
        -------
        [type]
            [description]
        """
        app = FastAPI()
        app = add_routes(self.routers, app)
        app.include_router(self.security.login)
        return app

        # open_api = app.openapi()

    @classmethod
    def from_yaml(cls, yaml_file: str):
        """[summary]

        Parameters
        ----------
        yaml_file : str
            [description]

        Returns
        -------
        [type]
            [description]
        """
        with open(yaml_file) as config:
            app_config = load(config, Loader)
        return cls(**app_config)

    @classmethod
    def from_json(cls, json_file: str):
        """[summary]

        Parameters
        ----------
        json_file : str
            [description]

        Returns
        -------
        [type]
            [description]
        """
        with open(json_file) as config:
            app_config = jsonload(config)
        return cls(**app_config)
