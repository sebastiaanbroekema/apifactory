"""module containing all router methods that are predefined
"""

# pylint: disable=E1101
# pylint: disable=W0613
from typing import Any, Callable, List, Optional, Type

from fastapi import Depends, Query, Request
from sqlalchemy.orm import Session

from autoapi.utils import (
    exclude_columns,
    not_found,
    param_invalid,
    primary_key_checker,
)


def getall_creator(
    method: Callable,
    model: Type,
    schema: Type,
    get_db,
    get_current_user,
    user_schema,
):
    """[summary]

    Parameters
    ----------
    method : Callable
        [description]
    model : Type
        [description]
    schema : Type
        [description]

    Returns
    -------
    [type]
        [description]
    """
    #  operation_id set for custom name instead of route in openapi
    @method(
        "/",
        response_model=List[schema],
    )
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
    model: Type,
    schema: Type,
    get_db,
    get_current_user,
    user_schema,
    primary_key_type: Any = int,
):
    """[summary]

    Parameters
    ----------
    method : Callable
        [description]
    model : Type
        [description]
    schema : Type
        [description]
    primary_key_type : Any, optional
        [description], by default int

    Returns
    -------
    [type]
        [description]
    """
    key_name, column = primary_key_checker(model)

    @method(
        "/{key}",
        response_model=schema,
    )
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
    model: Type,
    schema: Type,
    get_db,
    get_current_user,
    user_schema,
    primary_key_type: Any = int,
    excluded_columns: Optional[List] = None,
):
    """[summary]

    [extended_summary]

    Parameters
    ----------
    method : Callable
        [description]
    model : Type
        [description]
    schema : Type
        [description]
    primary_key_type : Any, optional
        [description], by default int

    Returns
    -------
    [type]
        [description]
    """

    key_name, column = primary_key_checker(model)
    # schema = model_with_optional_fields(schema)

    @method("/{key}")
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
    model: Type,
    schema: Type,
    get_db,
    get_current_user,
    user_schema,
    excluded_columns: Optional[list] = None,
):
    """[summary]

    Parameters
    ----------
    method : Callable
        [description]
    model : Type
        [description]
    schema : Type
        [description]
    excluded_columns : Optional[list], optional
        [description], by default None

    Returns
    -------
    [type]
        [description]
    """

    @method("/")
    def post(
        request: schema,
        db: Session = Depends(get_db),
        current_user: user_schema = Depends(get_current_user),
    ):
        # schema = model_with_optional_fields(schema)
        original_request = request
        request = request.dict()
        if excluded_columns:
            request = exclude_columns(request, excluded_columns)
        db.add(model(**request))
        db.commit()
        return original_request

    return post


def delete_creator(
    method: Callable,
    model: Type,
    get_db,
    get_current_user,
    user_schema,
    primary_key_type: Any = int,
):
    """[summary]

    Parameters
    ----------
    method : Callable
        [description]
    model : Type
        [description]
    primary_key_type : Any, optional
        [description], by default int

    Returns
    -------
    [type]
        [description]
    """

    key_name, column = primary_key_checker(model)

    @method("/{key}")
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
        return f"recored with primary key: {key} deleted"

    return delete
