"""various util functions for apifactory

"""
# pylint: disable=E0611
from typing import Type
from fastapi import HTTPException, status

from pydantic import BaseModel, ValidationError


class PrimaryKeyAmountError(Exception):
    """Exception raised for errors in the primary key."""

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


def not_found(model: str, id_name: str, model_id: int):
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"model: {model.__name__} does not have {id_name} {model_id}",
    )


def param_invalid(model: str, parameter: str):
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=f"model: {model.__name__} does not accept parameter {parameter}",
    )


def schema_error(schema, reponse_dict):
    """[summary]

    Parameters
    ----------
    schema : [type]
        [description]
    reponse_dict : [type]
        [description]

    Raises
    ------
    ValidationError
        [description]
    """
    try:
        schema(**reponse_dict)
        print(dir(schema))
    except ValidationError as error:
        raise ValidationError from error


def primary_key_checker(model: Type):
    """checks the amount of primary key columns


    Parameters
    ----------
    model : Type
        a SQLalchemy model containing the table details.

    Returns
    -------
    [tuple]
        [returns keyname and the column object that is the primary key]

    Raises
    ------
    PrimaryKeyAmountError
        [is raised if there are more than 1 primary key columns]
    """

    primary_keys = model.__table__.primary_key.columns.values()
    if not len(primary_keys) == 1:
        raise PrimaryKeyAmountError
    key_name = primary_keys[0].name
    column = getattr(model, key_name)
    return key_name, column


def model_with_optional_fields(model: Type[BaseModel]) -> Type[BaseModel]:
    """
    Generate a `BaseModel` class with
    all the same fields as `model` but as optional
    """

    class OptionalModel(model):
        """Class to contain optional version for all fields in model"""

    for field in OptionalModel.__fields__.values():
        field.required = False

    # for generated schema for example (can be removed)
    OptionalModel.__name__ = f"Optional{model.__name__}"

    return OptionalModel


def exclude_columns(request: dict, excluded_columns: list):
    return {i: j for i, j in request.items() if i not in excluded_columns}


def add_routes(routers, app):

    for router_name in routers.router_names:
        app.include_router(getattr(routers, router_name))
    return app


def open_api_alter(open_api):
    for schema in list(open_api["components"]["schemas"].keys()):
        if "Optional" in schema:
            open_api["components"]["schemas"].pop(schema)
    return open_api
