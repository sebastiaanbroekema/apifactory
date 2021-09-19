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

from typing import Optional, Tuple
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
    """Class that contains the table and viewnames of the database.
    DataBase class will add Models as atributes for further use in ApiFactory.
    """

    table_names: set = set()
    view_names: set = set()


DTYPES = {"VARCHAR": VARCHAR, "NCHAR": NCHAR, "INTEGER": INTEGER, "NVARCHAR": NVARCHAR}


def add_to_metadata(
    name: str, primary_keys, metadata: MetaData, engine
) -> Tuple[Table, MetaData]:
    """Helper function for creating virtual primary keys for views.

    :param name: Name of the view in the database.
    :type name: str
    :param primary_keys: List containing lists of primary key names and datatypes
    :type primary_keys:
    :param metadata: SQL metadata instance. Used for automatically detecting other columns
    :type metadata: MetaData
    :param engine: Engine instance that connects to the database
    :type engine: [type]
    :return: Returns table instancese and the modified MetaData instance.
    :rtype: Tuple[Table, MetaData]
    """

    columns = [
        Column(key[0], DTYPES.get(key[1]), primary_key=True) for key in primary_keys
    ]

    created_table = Table(name, metadata, autoload=True, autoload_with=engine, *columns)
    return created_table, metadata


class Database:
    # pylint: disable=C0301
    """setup database connection, automatically detect
    all eligable tables in the connected database.

    :param database_url: Database connection string.
    :type database_url: str
    :param engine_kwargs: Dictionary containing configuration for the database engine, defaults to None
    :type engine_kwargs: Optional[dict], optional
    :param local_session_kwargs: Arguments to be applied to sql session maker. If no session arguments are defined autocommit and autoflush are turned off, defaults to None
    :type local_session_kwargs: Optional[dict], optional
    :param views: Dictionary containing view name (key) and list of primarykey name datatype pairs. Only views defined in this dictionary will be added to the api, defaults to None
    :type views: Optional[dict], optional

    basic use only add a database connection string


    >>> Database("connection_string")

    If you want to pass arguments to the database engine. You must define engine_kwargs.
    For instance using sqlite databases in FastAPI require you to set check_same_thread to False.


    >>> # engine kwargs required for a sqlite database
    >>> engine_kwargs = {'engine_kwargs':{'connect_args':"check_same_thread": False}}
    >>> Database("connection_string", engine_kwargs)


    To configure the database session created inside the DataBase class you need to pass
    local_session_kwargs. For instance if you want to enable autocommit
    and autoflush you can add those in a local_session_kwargs.


    >>> local_session_kwargs = dict(
                autocommit=True,
                autoflush=True,
            )
    >>> Database("connection_string", local_session_kwargs=local_session_kwargs)


    If your database has views you want to enable get requests
    from you need to add the views dictionary.
    Since SQL Alchemy requires a primary key,
    for the auto detect mechanism for objects in the database, views cannot be added automatically.
    To add views to your API you need to input 1) the name of the view 2)
    the name and datatype of the primary key(s).

    >>> views = {'View_name':
    ...    [
    ...    [Primary key column2, Datatype primary key column2],
    ...    [Primary key column2, Datatype primary key column2]
    ...    ]
    ... }
    >>> Database("connection_string", views=views)
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
        """simple helper generator for handeling local database sessions.
        Passed internally to all endpoints.

        :yield: returns a local_session instance for use inside an api endpoint.
        :rtype:
        """
        db = self.local_session()
        try:
            yield db
        finally:
            db.close()

    def auto_create_models(self) -> Models:
        """method for automatically detecting sql tables
        and converting them into SQL alchemy models

        :return: object containing all detected sql tables and views.
        :rtype: Models
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
