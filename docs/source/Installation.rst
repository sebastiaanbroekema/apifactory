Getting started
===============


With apifactory you can automatically create an API on existing sql databases. Apifactory supports any SQL database dat is supported by sqlalchemy.
Apifactory has supports creating endpoints on both tables and views, views are limitted to only get requests.

Since apifactory uses FastAPI the resulting app also has automatic openapi (formally swagger) and redoc documentation pages.

To install apifactory you can simply use pip:

.. code-block:: console

   pip install apifactory

Simple app setup
****************

WIth some simple configuration you can automatically create a FastAPI app based on the contents of your database.
The most important parts of the configuration are the database connection string, a key for JWT encryption an optional dictionary containing configuration for your endpoints and further configuration for your app.
FInally you need to submit the name of the name of the database table containing user login data for user authentication and access to the database.

.. code-block:: python

   from apifactory.app_factory import ApiFactory

    dburl = "connection string to database"

    key = "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"
    # completely optional
    configuration = {
        "table_1": {
            "excluded_columns_put": ["Personid", "createdDate"],
            "excluded_columns_post": ["Personid", "createdDate"],
        },
        "table_2": {"excluded_columns_put": ["primarykey"]}
    }
    usermodel_name = "Users"

    app = ApiFactory(dburl, usermodel_name, key, configuration).app_factory()

This created app can subsequently be used with any ASGI server for example with uvicorn.


.. code-block:: console

    uvicorn <file containing the app>:app <further uvicorn args>


You now have a running instance of an app created by apifacotry.
