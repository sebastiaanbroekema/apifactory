"""Module containing ApiFactory class.
Used for creating a fully fledged instance of a FastAPI app,
that nearly automatically handles and secures your api.
"""

from json import load as jsonload
from yaml import load, Loader
from fastapi import FastAPI
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware


from apifactory.route_factory import Routers
from apifactory.security import Security
from apifactory.utils import add_routes
from apifactory.database import Database
from apifactory.schemas import Schemas


class ApiFactory:
    # pylint: disable=C0301
    """Factory class for building a complete FastAPI app from configuration.
    Configuration can be provided by directly calling __init__ or by reading in json or yaml files.


    :param database_url: Connection string to the database containing the data.
    :type database_url: str
    :param usermodel_name: Name of the database table that contains the information about users for the api.
    :type usermodel_name: str
    :param jwt_key: Key to use for hashing of the jwt. required for security purposes.
    :type jwt_key: str
    :param config: Dictionary containing further configuration options to the application.
    :type config: dict
    :param database: Class handeling the Database connection and tables, defaults to Database
    :type database: Database, optional
    :param schemas: Class handeling the pydantic schemas, defaults to Schemas
    :type schemas: Schemas, optional
    :param security: Security class handeling authentication and encryption/decryption of the JWT, defaults to Security
    :type security: Security, optional
    :param routers: Class for building the router objects used for creating the routes in the application, defaults to Routers
    :type routers: Routers, optional


    >>> app = ApiFactory().app_factory()
    """
    # pylint: enable=C0301

    def __init__(
        self,
        database_url: str,
        usermodel_name: str,
        jwt_key: str,
        config: dict,
        database: Database = Database,
        schemas: Schemas = Schemas,
        security: Security = Security,
        routers: Routers = Routers,
        **kwargs,
    ):

        self.db = database(
            database_url,
            engine_kwargs=kwargs.get("engine_kwargs", None),
            views=config.get("views", None),
        )
        rate_limit = kwargs.get("ratelimit")

        self.limiter = Limiter(
            key_func=get_remote_address,
            default_limits=[rate_limit],
            enabled=bool(rate_limit),
        )

        self.schemas = schemas(self.db.models)
        usermodel = getattr(self.db.models, usermodel_name)
        userschema = getattr(self.schemas, usermodel_name)
        self.security = security(usermodel, self.db.get_db, jwt_key)

        self.routers = routers(
            self.db.models,
            self.schemas,
            config,
            self.db.get_db,
            self.security.get_current_user,
            userschema,
        )
        self.config = config

    def app_factory(self) -> FastAPI:
        """Method for creating the FastAPI app.
        Automatically adds a rate limiter to the app.
        Ratelimitter will be inactive if configuration does not specify a ratelimit.


        :return: Generated FastAPI object with all the routes added.
        ready to be used in uvicorn or your asgi application of choice.
        :rtype: FastAPI

        >>> somevalid_config = {}
        >>> app = ApiFactory(somevalid_config).app_factory()

        """

        app = FastAPI()

        app.state.limiter = self.limiter
        app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
        app.add_middleware(SlowAPIMiddleware)
        app = add_routes(self.routers, app)
        app.include_router(self.security.login)
        return app

    @classmethod
    def from_yaml(
        cls,
        yaml_file: str,
        encoding: str = "utf8",
        **kwargs,
    ):
        """Method to instantiate ApiFacotry from a yaml file.
        Offers support for kwargs

        :param yaml_file: Path to yaml file containing valid configuration for ApiFactory
        :type yaml_file: str
        :param encoding: Type of file encoding, defaults to 'utf8'
        :type encoding: str, optional
        :return: Instantiated ApiFactory object with the configuration
        provided by yaml file and kwargs
        :rtype: ApiFactory

        >>> app = ApiFactory.from_yaml(yaml_file)

        Additionally from_yaml accepts **kwargs.
        These are mainly for use of user defined classes inside of Apifactory.
        These custom classes can be used to override default behaviour of ApiFactory.
        The keys for these arguments should be accepted by ApiFactory.__init__


        >>> from apifactory.security import Security
        >>> class CustomSecurity(Security):
        ...    "some custom code goes here"
        >>> app = ApiFactory.from_yaml(yaml_file, security=CustomSecurity)

        """

        with open(yaml_file, encoding=encoding) as config:
            app_config = load(config, Loader)
        app_config = app_config | kwargs
        return cls(**app_config)

    @classmethod
    def from_json(cls, json_file: str, encoding: str = "utf8", **kwargs):
        """[summary]

        :param json_file: Path to json file containing valid configuration for ApiFactory.
        :type json_file: str
        :param encoding: Type of file encoding, defaults to 'utf8'
        :type encoding: str, optional
        :return: Instantiated ApiFactory object with the
        configuration provided by yaml file and kwargs
        :rtype: ApiFactory


        >>> app = ApiFactory.from_json(json_file)

        Additionally from_json accepts **kwargs.
        These are mainly for use of user defined classes inside of Apifactory.
        These custom classes can be used to override default behaviour of ApiFactory.
        The keys for these arguments should be accepted by ApiFactory.__init__


        >>> from apifactory.security import Security
        >>> class CustomSecurity(Security):
        ...    "some custom code goes here"
        >>> app = ApiFactory.from_json(json_file, security=CustomSecurity)
        """

        with open(json_file, encoding=encoding) as config:
            app_config = jsonload(config)
        app_config = app_config | kwargs
        return cls(**app_config)
