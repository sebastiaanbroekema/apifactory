"""for generating an entire app
"""
# pylint: disable=E1101
# from typing import List


from fastapi import FastAPI

# from fastapi.routing import APIRoute

from autoapi.route_factory import Routers
from autoapi.security import Security
from autoapi.utils import add_routes
from autoapi.database import Database
from autoapi.schemas import Schemas


SECRET_KEY = "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


class AutoAPI:
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
