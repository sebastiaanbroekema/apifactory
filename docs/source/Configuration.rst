Configuration
=============

Autoapi is highly configurable. Both the endpoints themselfs and FastAPI app can be configured by using custom classes.


Custom classes
**************

The ApiFactory Class can be instanciated with the custom classes provided by the user to override default behaviour.
The general gist of this is shown below.

.. code-block:: python

    from apifactory.app_factory import ApiFactory
    from apifactory.security import Security


    class CustomSecurity(Security):
       "some custom code goes here"


    app = ApiFactory.from_yaml(yaml_file, security=CustomSecurity)


In this example Secuirty is imported and a custom class is written that inherits from Security.
Custom code should be added to the CustomSecurity class, which can then be used in the instanciation of ApiFactory. This can be done in all instanciation methods ApiFacotry provides: from configuration json/yaml files or via direct instantion of the class in a python script.



Configuation of the API
***********************

Apifacotry supports numerous ways to configure the API that is generated. Configuration can be supplied in json or yaml format. Alternatively configuration can be supplied directly in a python script that instantiates ApiFacotry.

Below is a yaml example of supported options.

.. code-block:: yaml

    config:
        Persons:
            excluded_columns_post:
            - Personid
            - createdDate
            excluded_columns_put:
            - Personid
            - createdDate
        test_table:
            excluded_columns_put:
            - primarykey
        views:
            selection_view:
            -
                - Personid
                - INTEGER
    database_url: sqlite:///tests/testdb/test.db
    jwt_key: 09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7
    usermodel_name: Users
    ratelimit: 1/hour
    engine_kwargs:
        connect_args:
            "check_same_thread": False

The config element specifies the configuration for the endpoints and if there are any views in the database to be turned into an endpoint.
Each table in the database that you wish to configure you can decide if certain columns must be excluded in post or put requests. A potential usecase for this is when the database handles the generation of primary keys or the content of a specific column.

For views you must specify the names of the views you want to include and provide a a list of column name and datatype pairs. These column name and datatype pairs will be used to generate a 'virtual' primary key to the view. This allows SQLAlchemy to autodetect all the other columns in the view and infer their datatype.

In addition there are configuration options for the application itself.

- database_url must contain the connection string for the database.
- jwt_key is used to specify the key used for jwt encryption.
- usermodel_name is used to specify which table in the database contains user information for login.
- ratelimit is an optional element. It can be used to specify a request ratelimit per user session. Constrains over multiple timeperiods can be defined for example: 10/hour;100/day;2000/5years.
- engine_kwargs arguments to give the SQLAlchemy engine.
- More options to follow
