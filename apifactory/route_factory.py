"""route factory
"""
# pylint: disable=E1101
# pylint: disable=W0613
from typing import Type

from fastapi import APIRouter

from apifactory.router_methods import (
    get_id_creator,
    getall_creator,
    put_creator,
    post_creator,
    delete_creator,
)
from apifactory.utils import (
    model_with_optional_fields,
)


class Routers:
    """contains all the routers generated"""

    def __init__(
        self, models, schemas, configs, get_db, get_current_user, user_schema
    ) -> None:
        self.router_names: set = set()
        self.routers = self.create_routers(
            models, schemas, configs, get_db, get_current_user, user_schema
        )

    def create_routers(
        self, models, schemas, configs, get_db, get_current_user, user_schema
    ):
        """[summary]

        Parameters
        ----------
        models : [type]
            [description]
        schemas : [type]
            [description]
        configs : [type]
            [description]
        get_db : [type]
            [description]
        get_current_user : [type]
            [description]
        user_schema : [type]
            [description]
        """
        for model_name in models.table_names:
            config = configs.get(model_name, {})
            config["route"] = f"/{model_name}"
            schema = getattr(schemas, model_name)
            model = getattr(models, model_name)
            created_router = self.router_creator(
                model, schema, config, get_db, get_current_user, user_schema
            )
            setattr(self, model_name, created_router)
            self.router_names.add(model_name)
        return self

    @staticmethod
    def router_creator(
        model: Type,
        schema: Type,
        modelconfig: dict,
        get_db,
        get_current_user,
        user_schema,
    ):
        """[summary]

        Parameters
        ----------
        model : Type
            [description]
        schema : Type
            [description]
        modelconfig : dict
            [description]

        Returns
        -------
        [type]
            [description]
        """
        route = f"{modelconfig['route']}"

        router = APIRouter(prefix=route, tags=[model.__name__])
        router_routes = {
            "get": router.get,
            "post": router.post,
            "put": router.put,
            "delete": router.delete,
        }
        schema_opt = model_with_optional_fields(schema)
        getall_creator(
            method=router_routes["get"],
            model=model,
            schema=schema,
            get_db=get_db,
            method_kwargs=modelconfig.get("get_kwargs", {}),
            get_current_user=get_current_user,
            user_schema=user_schema,
        )
        get_id_creator(
            method=router_routes["get"],
            model=model,
            schema=schema,
            get_db=get_db,
            method_kwargs=modelconfig.get("get_id_kwargs", {}),
            get_current_user=get_current_user,
            user_schema=user_schema,
        )
        put_creator(
            router_routes["put"],
            model,
            schema_opt,
            excluded_columns=modelconfig.get("excluded_columns_put", None),
            get_db=get_db,
            method_kwargs=modelconfig.get("put_kwargs", {}),
            get_current_user=get_current_user,
            user_schema=user_schema,
        )
        post_creator(
            router_routes["post"],
            model,
            schema_opt,
            excluded_columns=modelconfig.get("excluded_columns_post", None),
            get_db=get_db,
            method_kwargs=modelconfig.get("post_kwargs", {}),
            get_current_user=get_current_user,
            user_schema=user_schema,
        )
        delete_creator(
            router_routes["delete"],
            model,
            get_db=get_db,
            method_kwargs=modelconfig.get("delete_kwargs", {}),
            get_current_user=get_current_user,
            user_schema=user_schema,
        )

        return router
