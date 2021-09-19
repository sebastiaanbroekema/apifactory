"""Module containing the factory class that creates all router objects for the API.
"""
# pylint: disable=E1101
# pylint: disable=W0613
from typing import Callable

from sqlalchemy import Table
from pydantic import BaseModel

from fastapi import APIRouter

from apifactory.router_methods import (
    get_id_creator,
    getall_creator,
    put_creator,
    post_creator,
    delete_creator,
)
from apifactory.utils import (
    model_with_optional_fields,
)


class Routers:
    # pylint: disable=C0301
    """Creates and stores all routers created for the API.


    :param models: Models object containing all SQLalchemy models for the API.
    :type models: Models
    :param schemas: Schemas object containing all pydantic schemas for the API.
    :type schemas: Schemas
    :param configs: Dictionary containing the configuration for the routers.
    :type configs: dict
    :param get_db: Function to acquire a database session.
    :type get_db: Callable
    :param get_current_user: Function to acquire and verify the current user.
    :type get_current_user: [Callable]
    :param user_schema: Pydantic schema describing user information.
    :type user_schema: BaseModel


    Routers requires input from various other classes in apifactory.
    It needs access to the sqlalchemy table models for querying the database,
    pydantic schemas for converting table output to json and json to table input
    and the security class to handle access to the endpoints.


    >>> from apifactory.database import Database
    >>> from apifactory.schemas import Schemas
    >>> from apifactory.security import Security
    >>> config = { containing router configuration}
    >>> db = Database(**{database args})
    >>> schemas = Schemas(**{schemas args})
    >>> security = Security(**{security args})
    >>> routers = Routers(
    ...    db.models,
    ...    schemas,
    ...    config,
    ...    db.get_db,
    ...    security.get_current_user,
    ...    security.user_schema
    ...    )


    The resulting object can be used to register routes in a FastAPI app by using the add_routers function from apifactory utils.


    >>> from fastapi import FastAPI
    >>> from apifactory.utils import add_routers
    >>> app = FastAPI()
    >>> app = add_routers(routers, app)



    """
    # pylint: enable=C0301

    def __init__(
        self, models, schemas, configs, get_db, get_current_user, user_schema
    ) -> None:

        self.router_names: set = set()
        self.routers = self.create_routers(
            models, schemas, configs, get_db, get_current_user, user_schema
        )

    def create_routers(
        self, models, schemas, configs, get_db, get_current_user, user_schema
    ):
        """method for building

        :param models: Models object containing all SQLalchemy models for the API.
        :type models: Models
        :param schemas: Schemas object containing all pydantic schemas for the API.
        :type schemas: Schemas
        :param configs: Dictionary containing the configuration for the routers.
        :type configs: dict
        :param get_db: Function to acquire a database session.
        :type get_db: Callable
        :param get_current_user: Function to acquire and verify the current user.
        :type get_current_user: [Callable]
        :param user_schema: Pydantic schema describing user information.
        :type user_schema: BaseModel
        """
        for model_name in models.table_names:
            config = configs.get(model_name, {})
            config["route"] = f"/{model_name}"
            schema = getattr(schemas, model_name)
            model = getattr(models, model_name)
            is_view = model_name in models.view_names
            created_router = self.router_creator(
                model, schema, config, get_db, get_current_user, user_schema, is_view
            )
            setattr(self, model_name, created_router)
            self.router_names.add(model_name)
        return self

    @staticmethod
    def router_creator(
        model: Table,
        schema: BaseModel,
        modelconfig: dict,
        get_db: Callable,
        get_current_user: Callable,
        user_schema: BaseModel,
        is_view: bool,
    ) -> APIRouter:
        # pylint: disable=C0301
        """Method for creating a single router instance for a specific table or view in the database.
        Creates a get all, get, post, put and delete endpoint for tables and a get all, get endpoint for views.

        :param model: SQLalchemy model for the table containing endpoint data.
        :type model: Table
        :param schema: Pydantic schema describing input/output for the endpoints..
        :type schema: BaseModel
        :param modelconfig: Configuration for the endpoints.
        :type modelconfig: dict
        :param get_db: Function to acquire a database session.
        :type get_db: Callable
        :param get_current_user: Function to acquire and verify the current user.
        :type get_current_user: Callable
        :param user_schema: Pydantic schema describing user information.
        :type user_schema: BaseModel
        :param is_view: Flag indicating if the input is a view or not. Toggling which endpoints to create.
        :type is_view: bool
        :return: Router object for the specific database table or view.
        :rtype: APIRouter
        """
        # pylint: enable=C0301
        route = f"{modelconfig['route']}"

        router = APIRouter(prefix=route, tags=[model.__name__])
        router_routes = {
            "get": router.get,
            "post": router.post,
            "put": router.put,
            "delete": router.delete,
        }
        schema_opt = model_with_optional_fields(schema)

        getall_creator(
            method=router_routes["get"],
            model=model,
            schema=schema,
            get_db=get_db,
            method_kwargs=modelconfig.get("get_kwargs", {}),
            get_current_user=get_current_user,
            user_schema=user_schema,
        )
        get_id_creator(
            method=router_routes["get"],
            model=model,
            schema=schema,
            get_db=get_db,
            method_kwargs=modelconfig.get("get_id_kwargs", {}),
            get_current_user=get_current_user,
            user_schema=user_schema,
        )
        if is_view:
            return router
        put_creator(
            router_routes["put"],
            model,
            schema_opt,
            excluded_columns=modelconfig.get("excluded_columns_put", None),
            get_db=get_db,
            method_kwargs=modelconfig.get("put_kwargs", {}),
            get_current_user=get_current_user,
            user_schema=user_schema,
        )
        post_creator(
            router_routes["post"],
            model,
            schema_opt,
            excluded_columns=modelconfig.get("excluded_columns_post", None),
            get_db=get_db,
            method_kwargs=modelconfig.get("post_kwargs", {}),
            get_current_user=get_current_user,
            user_schema=user_schema,
        )
        delete_creator(
            router_routes["delete"],
            model,
            get_db=get_db,
            method_kwargs=modelconfig.get("delete_kwargs", {}),
            get_current_user=get_current_user,
            user_schema=user_schema,
        )

        return router
