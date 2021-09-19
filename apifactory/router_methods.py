"""module containing all create route methods that are predefined.
"""

# pylint: disable=E1101
# pylint: disable=W0613
# pylint: disable=C0301
from typing import Any, Callable, List, Optional, Union

from fastapi import Depends, Query, Request
from sqlalchemy.orm import Session
from sqlalchemy import Table
from pydantic import BaseModel, Field

from apifactory.utils import (
    exclude_columns,
    not_found,
    param_invalid,
    primary_key_checker,
    inserter,
)


def getall_creator(
    method: Callable,
    model: Table,
    schema: BaseModel,
    get_db: Callable,
    get_current_user: Callable,
    user_schema: BaseModel,
    method_kwargs: dict,
) -> Callable:
    """Function for creating a get endpoint that retrives all entries.


    :param method: FastAPI Router method to decorate the endpoint function with.
    :type method: Callable
    :param model: SQLalchemy model for the table containing endpoint data.
    :type model: Table
    :param schema: Pydantic schema describing input/output for the endpoints.
    :type schema: BaseModel
    :param get_db: Function to acquire a database session.
    :type get_db: Callable
    :param get_current_user: Function to acquire and verify the current user.
    :type get_current_user: Callable
    :param user_schema: Pydantic schema describing user information.
    :type user_schema: BaseModel
    :param method_kwargs: Key word arguments to add to the router method.
    :type method_kwargs: dict
    :return: Endpoint function.
    :rtype: Callable
    """
    #  operation_id set for custom name instead of route in openapi
    @method("/", response_model=List[schema], **method_kwargs)
    def get_all(
        request: Request,
        db: Session = Depends(get_db),
        limit: int = Query(100),
        current_user: user_schema = Depends(get_current_user),
    ):
        response = db.query(model)
        for param, value in request.query_params.items():
            if param == "limit":
                continue
            if not hasattr(model, param):
                param_invalid(model, param)
            column = getattr(model, param, None)
            response = response.filter(column == value)
        return response.limit(limit).all()

    return get_all


def get_id_creator(
    method: Callable,
    model: Table,
    schema: BaseModel,
    get_db: Callable,
    get_current_user: Callable,
    user_schema: BaseModel,
    method_kwargs: dict,
    primary_key_type: Any = int,
) -> Callable:
    """Generate an get endpoint to retrive elements by primarykey value.



    :param method: FastAPI Router method to decorate the endpoint function with.
    :type method: Callable
    :param model: SQLalchemy model for the table containing endpoint data.
    :type model: Table
    :param schema: Pydantic schema describing input/output for the endpoints.
    :type schema: BaseModel
    :param get_db: Function to acquire a database session.
    :type get_db: Callable
    :param get_current_user: Function to acquire and verify the current user.
    :type get_current_user: Callable
    :param user_schema: Pydantic schema describing user information.
    :type user_schema: BaseModel
    :param method_kwargs: Key word arguments to add to the router method.
    :type method_kwargs: dict
    :param primary_key_type: Type of the primary key to use in endpoint, defaults to int
    :type primary_key_type: Any, optional
    :return: Endpoint function.
    :rtype: Callable
    """
    key_name, column = primary_key_checker(model)

    @method("/{key}", response_model=schema, **method_kwargs)
    def get_id(
        key: primary_key_type,
        db: Session = Depends(get_db),
        current_user: user_schema = Depends(get_current_user),
    ):
        response = db.query(model).filter(column == key).first()
        if not response:
            not_found(model, key_name, key)
        return response

    return get_id


def put_creator(
    method: Callable,
    model: Table,
    schema: BaseModel,
    get_db: Callable,
    get_current_user: Callable,
    user_schema: BaseModel,
    method_kwargs: dict,
    primary_key_type: Any = int,
    excluded_columns: Optional[List] = None,
) -> Callable:
    """Creates put endpoint for updating single entries in the database.

    :param method: FastAPI Router method to decorate the endpoint function with.
    :type method: Callable
    :param model: SQLalchemy model for the table containing endpoint data.
    :type model: Table
    :param schema: Pydantic schema describing input/output for the endpoints.
    :type schema: BaseModel
    :param get_db: Function to acquire a database session.
    :type get_db: Callable
    :param get_current_user: Function to acquire and verify the current user.
    :type get_current_user: Callable
    :param user_schema: Pydantic schema describing user information.
    :type user_schema: BaseModel
    :param method_kwargs: Key word arguments to add to the router method.
    :type method_kwargs: dict
    :param primary_key_type: Type of the primary key to use in endpoint, defaults to int
    :type primary_key_type: Any, optional
    :param excluded_columns: List contaning columns to exclude from the put request. For example primary key should not be updated, defaults to None
    :type excluded_columns: Optional[List], optional
    :return: Endpoint function.
    :rtype: Callable
    """

    key_name, column = primary_key_checker(model)
    # schema = model_with_optional_fields(schema)

    @method("/{key}", **method_kwargs)
    async def update(
        request: schema,
        key: primary_key_type,
        db: Session = Depends(get_db),
        current_user: user_schema = Depends(get_current_user),
    ):
        db_item = db.query(model).filter(column == key)
        if not db_item.first():
            not_found(model, key_name, key)

        request = request.dict()
        if excluded_columns:
            request = exclude_columns(request, excluded_columns)
        db_item.update(request)
        db.commit()
        return "updated"

    return update


def post_creator(
    method: Callable,
    model: Table,
    schema: BaseModel,
    get_db: Callable,
    get_current_user: Callable,
    user_schema: BaseModel,
    method_kwargs: dict,
    excluded_columns: Optional[List] = None,
) -> Callable:
    """Creates a post endpoint for single or multiple entries into the database.


    :param method: FastAPI Router method to decorate the endpoint function with.
    :type method: Callable
    :param model: SQLalchemy model for the table containing endpoint data.
    :type model: Table
    :param schema: Pydantic schema describing input/output for the endpoints.
    :type schema: BaseModel
    :param get_db: Function to acquire a database session.
    :type get_db: Callable
    :param get_current_user: Function to acquire and verify the current user.
    :type get_current_user: Callable
    :param user_schema: Pydantic schema describing user information.
    :type user_schema: BaseModel
    :param method_kwargs: Key word arguments to add to the router method.
    :type method_kwargs: dict
    :param excluded_columns: List contaning columns to exclude from the put request. For example primary key should not be updated, defaults to None
    :type excluded_columns: Optional[List], optional
    :return: Endpoint function.
    :rtype: Callable
    """

    @method("/", **method_kwargs)
    def post(
        request: Union[List[schema], schema],
        db: Session = Depends(get_db),
        current_user: user_schema = Depends(get_current_user),
    ):
        # schema = model_with_optional_fields(schema)
        original_request = request
        # if isinstance(request,list):
        #     insert_many(request,excluded_columns,db,model)
        # else:
        #     insert_single(request,excluded_columns,db,model)
        inserter(request, excluded_columns, db, model)

        return original_request

    return post


def delete_creator(
    method: Callable,
    model: Table,
    get_db: Callable,
    get_current_user: Callable,
    user_schema: BaseModel,
    method_kwargs: dict,
    primary_key_type: Any = int,
) -> Callable:
    """Creates an endpoint to delete multiple entries by request data.

    :param method: FastAPI Router method to decorate the endpoint function with.
    :type method: Callable
    :param model: SQLalchemy model for the table containing endpoint data.
    :type model: Table
    :param get_db: Function to acquire a database session.
    :type get_db: Callable
    :param get_current_user: Function to acquire and verify the current user.
    :type get_current_user: Callable
    :param user_schema: Pydantic schema describing user information.
    :type user_schema: BaseModel
    :param method_kwargs: Key word arguments to add to the router method.
    :type method_kwargs: dict
    :param primary_key_type: Type of the primary key to use in endpoint, defaults to int
    :type primary_key_type: Any, optional
    :return: Endpoint function.
    :rtype: Callable
    """

    key_name, column = primary_key_checker(model)

    class PrimaryKeyHolder(BaseModel):
        primary_key: primary_key_type = Field(alias=str(key_name))

    PrimaryKeyHolder.__name__ = f"Keyholder{model.__name__}"
    # PrimaryKeyHolder.__dict__[key_name] = PrimaryKeyHolder.__dict__.pop('primary_key')

    # PrimaryKeyHolder = create_model('PrimaryKeyHolder', key_name=primary_key_type)
    # namedtuple('PrimaryKeyHolder',[str(key_name)])

    @method("/", **method_kwargs)
    def delete_many(
        request: List[PrimaryKeyHolder],
        db: Session = Depends(get_db),
        current_user: user_schema = Depends(get_current_user),
    ):
        key_list = [pk.dict()["primary_key"] for pk in request]
        db_items = db.query(model).filter(column.in_(key_list))
        db_items.delete(synchronize_session=False)
        db.commit()
        return "records deleted"

    return delete_many


def delete_creator_id(
    method: Callable,
    model: Table,
    get_db: Callable,
    get_current_user: Callable,
    user_schema: BaseModel,
    method_kwargs: dict,
    primary_key_type: Any = int,
) -> Callable:
    """Creates an endpoint to delete a single entry by primary key.

    :param method: FastAPI Router method to decorate the endpoint function with.
    :type method: Callable
    :param model: SQLalchemy model for the table containing endpoint data.
    :type model: Table
    :param get_db: Function to acquire a database session.
    :type get_db: Callable
    :param get_current_user: Function to acquire and verify the current user.
    :type get_current_user: Callable
    :param user_schema: Pydantic schema describing user information.
    :type user_schema: BaseModel
    :param method_kwargs: Key word arguments to add to the router method.
    :type method_kwargs: dict
    :param primary_key_type: Type of the primary key to use in endpoint, defaults to int
    :type primary_key_type: Any, optional
    :return: Endpoint function.
    :rtype: Callable
    """

    key_name, column = primary_key_checker(model)

    @method("/{key}", **method_kwargs)
    def delete(
        key: primary_key_type,
        db: Session = Depends(get_db),
        current_user: user_schema = Depends(get_current_user),
    ):
        db_item = db.query(model).filter(column == key)
        if not db_item.first():
            not_found(model, key_name, key)
        db_item.delete(synchronize_session=False)
        db.commit()
        return f"record with primary key: {key} deleted"

    return delete
