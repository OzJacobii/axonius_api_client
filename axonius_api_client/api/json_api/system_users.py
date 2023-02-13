# -*- coding: utf-8 -*-
"""Models for API requests & responses."""
import dataclasses
import datetime
import typing as t

import marshmallow
import marshmallow_jsonapi

from .base import BaseModel, BaseSchema, BaseSchemaJson
from .custom_fields import SchemaBool, SchemaDatetime, SchemaPassword, get_field_dc_mm


class SystemUserSchema(BaseSchemaJson):
    """Pass."""

    email = marshmallow_jsonapi.fields.Str(allow_none=True)
    first_name = marshmallow_jsonapi.fields.Str(load_default="", dump_default="", allow_none=True)
    last_login = SchemaDatetime()
    last_name = marshmallow_jsonapi.fields.Str(load_default="", dump_default="", allow_none=True)
    last_updated = SchemaDatetime()
    password = SchemaPassword(load_default="", dump_default="", allow_none=True)
    pic_name = marshmallow_jsonapi.fields.Str(load_default="", dump_default="", allow_none=True)
    role_id = marshmallow_jsonapi.fields.Str(required=True)
    role_name = marshmallow_jsonapi.fields.Str(
        load_default=None, dump_default=None, allow_none=True
    )
    title = marshmallow_jsonapi.fields.Str(load_default=None, dump_default=None, allow_none=True)
    department = marshmallow_jsonapi.fields.Str(
        load_default=None, dump_default=None, allow_none=True
    )
    source = marshmallow_jsonapi.fields.Str()
    user_name = marshmallow_jsonapi.fields.Str(required=True)
    uuid = marshmallow_jsonapi.fields.Str(required=True)
    ignore_role_assignment_rules = SchemaBool(
        load_default=False, dump_default=False, allow_none=True
    )

    @staticmethod
    def get_model_cls() -> type:
        """Pass."""
        return SystemUser

    class Meta:
        """Pass."""

        type_ = "users_details_schema"


class SystemUserUpdateSchema(SystemUserSchema):
    """Pass."""

    last_login = SchemaDatetime(allow_none=True)

    class Meta:
        """Pass."""

        type_ = "users_schema"

    @staticmethod
    def get_model_cls() -> type:
        """Pass."""
        return SystemUserUpdate

    @marshmallow.pre_load
    def pre_load_fix(self, data, **kwargs) -> t.Union[dict, BaseModel]:
        """Pass."""
        data["email"] = data.get("email", "") or ""
        data["first_name"] = data.get("first_name", "") or ""
        data["last_name"] = data.get("last_name", "") or ""
        data["password"] = data.get("password", "") or ""
        return data

    @marshmallow.post_dump
    def post_dump_fixit(self, data: dict, **kwargs) -> dict:
        """Pass."""
        # PBUG: these should really just be ignored by rest api
        data.pop("last_updated", None)
        data.pop("last_login", None)
        data.pop("uuid", None)
        return data


@dataclasses.dataclass
class SystemUser(BaseModel):
    """Pass."""

    role_id: str
    user_name: str
    uuid: str

    email: t.Optional[str] = None
    first_name: t.Optional[str] = None
    id: t.Optional[str] = None
    last_login: t.Optional[datetime.datetime] = get_field_dc_mm(
        mm_field=SchemaDatetime(allow_none=True), default=None
    )
    last_name: t.Optional[str] = None
    last_updated: t.Optional[datetime.datetime] = get_field_dc_mm(
        mm_field=SchemaDatetime(allow_none=True), default=None
    )
    password: t.Optional[t.Union[t.List[str], str]] = None
    pic_name: t.Optional[str] = None
    role_name: t.Optional[str] = None
    title: t.Optional[str] = None
    department: t.Optional[str] = None
    source: t.Optional[str] = None
    ignore_role_assignment_rules: bool = False
    document_meta: t.Optional[dict] = dataclasses.field(default_factory=dict)

    @staticmethod
    def get_schema_cls() -> t.Optional[t.Type[BaseSchema]]:
        """Pass."""
        return SystemUserSchema

    @property
    def full_name(self) -> str:
        """Pass."""
        return " ".join([x for x in [self.first_name, self.last_name] if x])

    def __post_init__(self):
        """Pass."""
        if self.id is None and self.uuid is not None:
            self.id = self.uuid

    def to_dict_old(self, system_roles: t.List[dict]) -> dict:
        """Pass."""
        system_role = [x for x in system_roles if x["uuid"] == self.role_id][0]
        obj = self.to_dict()
        obj["role_obj"] = system_role
        obj["role_name"] = system_role["name"]
        obj["full_name"] = self.full_name
        return obj


@dataclasses.dataclass
class SystemUserUpdate(SystemUser):
    """Pass."""

    @staticmethod
    def get_schema_cls() -> t.Optional[t.Type[BaseSchema]]:
        """Pass."""
        return SystemUserUpdateSchema


class SystemUserCreateSchema(BaseSchemaJson):
    """Pass."""

    user_name = marshmallow_jsonapi.fields.Str(required=True)
    role_id = marshmallow_jsonapi.fields.Str(required=True)

    auto_generated_password = SchemaBool(load_default=False, dump_default=False)
    email = marshmallow_jsonapi.fields.Str(load_default="", dump_default="", allow_none=True)
    first_name = marshmallow_jsonapi.fields.Str(load_default="", dump_default="", allow_none=True)
    last_name = marshmallow_jsonapi.fields.Str(load_default="", dump_default="", allow_none=True)
    password = SchemaPassword(load_default="", dump_default="", allow_none=True)

    @staticmethod
    def get_model_cls() -> type:
        """Pass."""
        return SystemUserCreate

    class Meta:
        """Pass."""

        type_ = "create_user_schema"

    @marshmallow.validates_schema
    def validate_fields(self, data, **kwargs):
        """Pass."""
        errors = {}
        if not data.get("password") and not data.get("auto_generated_password"):
            errors["password"] = "Must supply a password if auto_generated_password is False"
            raise marshmallow.ValidationError(errors)


@dataclasses.dataclass
class SystemUserCreate(BaseModel):
    """Pass."""

    user_name: str
    role_id: str

    auto_generated_password: bool = False
    email: t.Optional[str] = None
    first_name: t.Optional[str] = None
    last_name: t.Optional[str] = None
    password: t.Optional[str] = get_field_dc_mm(
        mm_field=SchemaPassword(load_default="", dump_default="", allow_none=True), default=""
    )

    def __post_init__(self):
        """Pass."""
        self.email = self.email or ""
        self.first_name = self.first_name or ""
        self.last_name = self.last_name or ""
        self.password = self.password or ""

    @staticmethod
    def get_schema_cls() -> t.Optional[t.Type[BaseSchema]]:
        """Pass."""
        return SystemUserCreateSchema
