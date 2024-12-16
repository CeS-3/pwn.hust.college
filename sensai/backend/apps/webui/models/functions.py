from pydantic import BaseModel, ConfigDict
from typing import List, Union, Optional
import time
import logging

from sqlalchemy import Column, String, Text, BigInteger, Boolean

from apps.webui.internal.db import JSONField, Base, get_db
from apps.webui.models.users import Users

import json
import copy


from config import SRC_LOG_LEVELS

log = logging.getLogger(__name__)
log.setLevel(SRC_LOG_LEVELS["MODELS"])

####################
# Functions DB Schema
####################


class Function(Base):
    __tablename__ = "function"

    id = Column(String, primary_key=True)
    user_id = Column(String)
    name = Column(Text)
    type = Column(Text)
    content = Column(Text)
    meta = Column(JSONField)
    valves = Column(JSONField)
    is_active = Column(Boolean)
    is_global = Column(Boolean)
    updated_at = Column(BigInteger)
    created_at = Column(BigInteger)


class FunctionMeta(BaseModel):
    description: Optional[str] = None
    manifest: Optional[dict] = {}


class FunctionModel(BaseModel):
    id: str
    user_id: str
    name: str
    type: str
    content: str
    meta: FunctionMeta
    is_active: bool = False
    is_global: bool = False
    updated_at: int  # timestamp in epoch
    created_at: int  # timestamp in epoch

    model_config = ConfigDict(from_attributes=True)


####################
# Forms
####################


class FunctionResponse(BaseModel):
    id: str
    user_id: str
    type: str
    name: str
    meta: FunctionMeta
    is_active: bool
    is_global: bool
    updated_at: int  # timestamp in epoch
    created_at: int  # timestamp in epoch


class FunctionForm(BaseModel):
    id: str
    name: str
    content: str
    meta: FunctionMeta


class FunctionValves(BaseModel):
    valves: Optional[dict] = None


class FunctionsTable:

    def insert_new_function(
        self, user_id: str, type: str, form_data: FunctionForm
    ) -> Optional[FunctionModel]:

        function = FunctionModel(
            **{
                **form_data.model_dump(),
                "user_id": user_id,
                "type": type,
                "updated_at": int(time.time()),
                "created_at": int(time.time()),
            }
        )

        try:
            with get_db() as db:
                result = Function(**function.model_dump())
                db.add(result)
                db.commit()
                db.refresh(result)
                if result:
                    return FunctionModel.model_validate(result)
                else:
                    return None
        except Exception as e:
            print(f"Error creating tool: {e}")
            return None

    def get_function_by_id(self, id: str) -> Optional[FunctionModel]:
        try:
            with get_db() as db:

                function = db.get(Function, id)
                return FunctionModel.model_validate(function)
        except:
            return None

    def get_functions(self, active_only=False) -> List[FunctionModel]:
        with get_db() as db:

            if active_only:
                return [
                    FunctionModel.model_validate(function)
                    for function in db.query(Function).filter_by(is_active=True).all()
                ]
            else:
                return [
                    FunctionModel.model_validate(function)
                    for function in db.query(Function).all()
                ]

    def get_functions_by_type(
        self, type: str, active_only=False
    ) -> List[FunctionModel]:
        with get_db() as db:

            if active_only:
                return [
                    FunctionModel.model_validate(function)
                    for function in db.query(Function)
                    .filter_by(type=type, is_active=True)
                    .all()
                ]
            else:
                return [
                    FunctionModel.model_validate(function)
                    for function in db.query(Function).filter_by(type=type).all()
                ]

    def get_global_filter_functions(self) -> List[FunctionModel]:
        with get_db() as db:

            return [
                FunctionModel.model_validate(function)
                for function in db.query(Function)
                .filter_by(type="filter", is_active=True, is_global=True)
                .all()
            ]

    def get_global_action_functions(self) -> List[FunctionModel]:
        with get_db() as db:
            return [
                FunctionModel.model_validate(function)
                for function in db.query(Function)
                .filter_by(type="action", is_active=True, is_global=True)
                .all()
            ]

    def get_function_valves_by_id(self, id: str) -> Optional[dict]:
        with get_db() as db:

            try:
                function = db.get(Function, id)
                return function.valves if function.valves else {}
            except Exception as e:
                print(f"An error occurred: {e}")
                return None

    def update_function_valves_by_id(
        self, id: str, valves: dict
    ) -> Optional[FunctionValves]:
        with get_db() as db:

            try:
                function = db.get(Function, id)
                function.valves = valves
                function.updated_at = int(time.time())
                db.commit()
                db.refresh(function)
                return self.get_function_by_id(id)
            except:
                return None

    def get_user_valves_by_id_and_user_id(
        self, id: str, user_id: str
    ) -> Optional[dict]:

        try:
            user = Users.get_user_by_id(user_id)
            user_settings = user.settings.model_dump() if user.settings else {}

            # Check if user has "functions" and "valves" settings
            if "functions" not in user_settings:
                user_settings["functions"] = {}
            if "valves" not in user_settings["functions"]:
                user_settings["functions"]["valves"] = {}

            return user_settings["functions"]["valves"].get(id, {})
        except Exception as e:
            print(f"An error occurred: {e}")
            return None

    def update_user_valves_by_id_and_user_id(
        self, id: str, user_id: str, valves: dict
    ) -> Optional[dict]:

        try:
            user = Users.get_user_by_id(user_id)
            user_settings = user.settings.model_dump() if user.settings else {}

            # Check if user has "functions" and "valves" settings
            if "functions" not in user_settings:
                user_settings["functions"] = {}
            if "valves" not in user_settings["functions"]:
                user_settings["functions"]["valves"] = {}

            user_settings["functions"]["valves"][id] = valves

            # Update the user settings in the database
            Users.update_user_by_id(user_id, {"settings": user_settings})

            return user_settings["functions"]["valves"][id]
        except Exception as e:
            print(f"An error occurred: {e}")
            return None

    def update_function_by_id(self, id: str, updated: dict) -> Optional[FunctionModel]:
        with get_db() as db:

            try:
                db.query(Function).filter_by(id=id).update(
                    {
                        **updated,
                        "updated_at": int(time.time()),
                    }
                )
                db.commit()
                return self.get_function_by_id(id)
            except:
                return None

    def deactivate_all_functions(self) -> Optional[bool]:
        with get_db() as db:

            try:
                db.query(Function).update(
                    {
                        "is_active": False,
                        "updated_at": int(time.time()),
                    }
                )
                db.commit()
                return True
            except:
                return None

    def delete_function_by_id(self, id: str) -> bool:
        with get_db() as db:
            try:
                db.query(Function).filter_by(id=id).delete()
                db.commit()

                return True
            except:
                return False


Functions = FunctionsTable()
