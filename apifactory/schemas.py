""" module for auto generating schema from loaded in tables
"""
# pylint: disable=E0611
from typing import Container, Optional, Type

from pydantic import BaseConfig, BaseModel, create_model
from sqlalchemy.inspection import inspect
from sqlalchemy.orm.properties import ColumnProperty
import sqlalchemy.orm
import sqlalchemy.sql.sqltypes


class OrmConfig(BaseConfig):
    orm_mode = True


class Schemas:
    """[summary]"""

    def __init__(self, Models: object) -> None:
        """[summary]

        Parameters
        ----------
        Models : object
            output of database class stored in .models attribute
        """
        tables = [
            getattr(Models, x)
            for x in dir(Models)
            if (type(getattr(Models, x)) == sqlalchemy.orm.decl_api.DeclarativeMeta)
        ]
        for table in tables:
            # disabled false positve pylint error
            # pylint: disable=C0103
            table_name = str(table.__table__.name)
            # pylint: enable=C0103
            schema = self.sqlalchemy_to_pydantic(table, config=OrmConfig)
            setattr(self, table_name, schema)

    @staticmethod
    def sqlalchemy_to_pydantic(
        db_model: Type, *, config: Type = OrmConfig, exclude: Container[str] = ()
    ) -> Type[BaseModel]:
        """[summary]

        Parameters
        ----------
        db_model : Type
            [description]
        config : Type, optional
            [description], by default OrmConfig
        exclude : Container[str], optional
            [description], by default []

        Returns
        -------
        Type[BaseModel]
            [description]
        """
        mapper = inspect(db_model)
        fields = {}
        for attr in mapper.attrs:
            if isinstance(attr, ColumnProperty):
                if attr.columns:
                    name = attr.key
                    if name in exclude:
                        continue
                    column = attr.columns[0]
                    python_type: Optional[type] = None
                    if hasattr(column.type, "impl"):
                        if hasattr(column.type.impl, "python_type"):
                            python_type = column.type.impl.python_type
                    elif hasattr(column.type, "python_type"):
                        python_type = column.type.python_type
                    assert python_type, f"Could not infer python_type for {column}"
                    default = None
                    if column.default is None and not column.nullable:
                        default = ...
                    fields[name] = (python_type, default)
        pydantic_model = create_model(
            db_model.__name__, __config__=config, **fields  # type: ignore
        )
        return pydantic_model


# tables = [
#     getattr(Models, x)
#     for x in dir(Models)
#     if (type(getattr(Models, x)) == sqlalchemy.orm.decl_api.DeclarativeMeta)
# ]


# for table in tables:
#     # disabled false positve pylint error
#     # pylint: disable=C0103
#     table_name = str(table.__table__.name)
#     # pylint: enable=C0103
#     schema = sqlalchemy_to_pydantic(table, config=OrmConfig)
#     setattr(Schemas, table_name, schema)
