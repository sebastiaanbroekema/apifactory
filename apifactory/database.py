"""Module for generating the models for the API
models will be generated via the automap of SQLAlchemy.
Database tables require a primary key to be added.

Tables without a primary key can be faked via the following.

metadata = MetaData()
Table('table',metadata, Column('some_id', Integer,
primary_key=true), autoload=True, autoload_with=engine)
the other columns will be added automatically
this way you can fake a primary key without having one in the database.
"""

from typing import Optional
from sqlalchemy import (
    create_engine,
    Column,
    Table,
    MetaData,
    VARCHAR,
    NCHAR,
    INTEGER,
    NVARCHAR,
)
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.automap import automap_base


class Models:
    table_names: set = set()
    view_names: set = set()


DTYPES = {"VARCHAR": VARCHAR, "NCHAR": NCHAR, "INTEGER": INTEGER, "NVARCHAR": NVARCHAR}


def add_to_metadata(name, primary_keys, metadata, engine):
    """helper function for creating virtual primary keys for views.

    Parameters
    ----------
    name : [type]
        [description]
    primary_keys : [type]
        [description]
    metadata : [type]
        [description]
    engine : [type]
        [description]

    Returns
    -------
    [type]
        [description]
    """
    columns = [
        Column(key[0], DTYPES.get(key[1], key[1]), primary_key=True)
        for key in primary_keys
    ]

    created_table = Table(name, metadata, autoload=True, autoload_with=engine, *columns)
    return created_table, metadata


class Database:
    """setup database connection automatically detect
    all eligable tables in the connected database
    """

    def __init__(
        self,
        database_url: str,
        engine_kwargs: Optional[dict] = None,
        local_session_kwargs: Optional[dict] = None,
        views: Optional[dict] = None,
    ):

        if not engine_kwargs:
            engine_kwargs = dict()
        self.engine = create_engine(database_url, **engine_kwargs)

        if not local_session_kwargs:
            local_session_kwargs = dict(
                autocommit=False,
                autoflush=False,
            )
        self.views = views
        self.local_session = sessionmaker(bind=self.engine, **local_session_kwargs)
        self.models = self.auto_create_models()

    def get_db(self):
        """simple helper generator for handeling local sessions.

        Yields
        -------
        SessionLocal
            SessionLocal for access to the database in the backend
        """
        db = self.local_session()
        try:
            yield db
        finally:
            db.close()

    def auto_create_models(self):
        """method for automatically detecting sql tables
        and converting them into SQL alchemy models

        Returns
        -------
        Models
            object containing all detected sql tables
        """
        # Session = sessionmaker(bind=engine)
        models = Models()
        metadata = MetaData()
        if self.views:
            # create view instances in metadata object
            for view, primarykeys in self.views.items():
                _, metadata = add_to_metadata(view, primarykeys, metadata, self.engine)
                models.view_names.add(view)

        # use metadata to include created views / multicolumn primary keys
        base = automap_base(metadata=metadata)
        base.prepare(self.engine, reflect=True)
        # pylint: disable=W0212
        # add all tables to the Models class
        for key, value in base.classes._data.items():
            setattr(models, key, value)
            models.table_names.add(key)
        return models
