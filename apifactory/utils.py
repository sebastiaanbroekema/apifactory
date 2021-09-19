"""Various util functions for apifactory used throughout the project.

"""
# pylint: disable=E0611
from typing import Type, Callable
from functools import singledispatch

from fastapi import HTTPException, status, FastAPI
from pydantic import BaseModel
from sqlalchemy import Table


class PrimaryKeyAmountError(Exception):
    """Exception raised for errors in the amount of primary key columns."""

    def __init__(
        self,
    ):
        self.message = """
        Number of columns part of primary key to high.
        Either remove the table from your api.
        Or designate an alternative primary key
        """
        super().__init__(self.message)

    def __str__(self):
        return f"{self.message}"


def not_found(model: str, id_name: str, model_id: int) -> None:
    """Callback function for raising 404 errors

    :param model: Name of the model that raises the error
    :type model: str
    :param id_name: Column name of that raises the error
    :type id_name: str
    :param model_id: Model ID that raises the error
    :type model_id: int
    :raises HTTPException: Raises http 404 error if an entry in the database is not found
    """
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"model: {model.__name__} does not have {id_name} {model_id}",
    )


def param_invalid(model: str, parameter: str):
    """Callback function for raising 400 errors for missing parameters

    :param model: Name of the model that raises the error
    :type model: str
    :param parameter: Name of the parameter that raises the error
    :type parameter: str
    :raises HTTPException: Raises http 400 error if the user privodes an unsupported parameter.
    """
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=f"model: {model.__name__} does not accept parameter {parameter}",
    )


def primary_key_checker(model: Table):
    """checks the amount of primary key columns if amount > 1 raise PrimaryKeyAmountError.
    Otherwise return primary key name and the column object

    :param model:
    :type model: Table
    :raises PrimaryKeyAmountError: [description]
    :return: Primary key name and sqlalchemy column object.
    :rtype: Tuple[str, Column]
    """

    primary_keys = model.__table__.primary_key.columns.values()
    if not len(primary_keys) == 1:
        raise PrimaryKeyAmountError
    key_name = primary_keys[0].name
    column = getattr(model, key_name)
    return key_name, column


def model_with_optional_fields(model: Type[BaseModel]) -> Type[BaseModel]:
    """Generate a `BaseModel` class with
    all the same fields as `model` but as optional


    :param model: Pydantic model that needs to have optional fields
    :type model: Type[BaseModel]
    :return: Pydantic model that has all it's fields turned to optional fields.
    :rtype: Type[BaseModel]
    """

    class OptionalModel(model):
        """Class to contain optional version for all fields in model"""

    for field in OptionalModel.__fields__.values():
        field.required = False

    # for generated schema for example (can be removed)
    OptionalModel.__name__ = f"Optional{model.__name__}"

    return OptionalModel


def exclude_columns(request: dict, excluded_columns: list) -> dict:
    """Removes columns in a request that are not supported.

    :param request: post/put request parsed json dictionary containing the data.
    :type request: dict
    :param excluded_columns: Which columns to exclude
    :type excluded_columns: list
    :return: Dictionary that does not contain excluded columns
    :rtype: dict
    """
    return {i: j for i, j in request.items() if i not in excluded_columns}


def add_routes(routers, app: FastAPI) -> FastAPI:
    """Function that adds all routers from a Routers class to a FastAPI app.

    :param routers: Routers class containing all routers to be added to your app.
    :type routers: Routers
    :param app: FastAPI app instance.
    :type app: FastAPI
    :return: FastAPI app instance with added routers.
    :rtype: FastAPI
    """

    for router_name in routers.router_names:
        app.include_router(getattr(routers, router_name))
    return app


@singledispatch
def inserter(request: list, excluded_columns: list, db: Callable, model: Table):
    """Inserter function. Singledispatched to accept multiple entries or a single one.

    :param request: The request from the endpoint. Either a list or a single entry.
    :type request: list|BaseModel
    :param excluded_columns: List contaning columns to exclude from the db operation.
    :type excluded_columns: list
    :param db: Function to acquire a database session
    :type db: Callable
    :param model: SQLalchemy model for the database operation.
    :type model: Table
    """
    for content in request:
        content = content.dict()
        if excluded_columns:
            content = exclude_columns(content, excluded_columns)
        db.add(model(**content))
    db.commit()


@inserter.register
def _(request: BaseModel, excluded_columns: list, db: callable, model: Table):
    request = request.dict()
    if excluded_columns:
        request = exclude_columns(request, excluded_columns)
    db.add(model(**request))
    db.commit()
