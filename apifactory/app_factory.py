"""for generating an entire app
"""
# pylint: disable=E1101
# from typing import List


from fastapi import FastAPI

# from fastapi.routing import APIRoute

from apifactory.route_factory import Routers
from apifactory.security import Security
from apifactory.utils import add_routes
from apifactory.database import Database
from apifactory.schemas import Schemas


class ApiFactory:
    """[summary]"""

    def __init__(self, database_url, usermodel_name, key, config):
        self.db = Database(database_url)
        self.schemas = Schemas(self.db.models)
        usermodel = getattr(self.db.models, usermodel_name)
        userschema = getattr(self.schemas, usermodel_name)
        self.security = Security(usermodel, self.db.get_db, key)
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
