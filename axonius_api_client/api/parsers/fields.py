# -*- coding: utf-8 -*-
"""API models for working with adapters and connections."""
import copy
from typing import List

from ...constants import AGG_ADAPTER_NAME, AGG_ADAPTER_TITLE, ALL_NAME
from ...data_classes.fields import OperatorTypeMaps
from ...tools import strip_left, strip_right


def parse_fields(raw: dict) -> dict:
    """Parse all generic and adapter specific fields.

    Returns:
        :obj:`dict`: parsed generic and adapter specific fields
    """
    parsed = {}
    parsed[AGG_ADAPTER_NAME] = parse_schemas(
        adapter_name=AGG_ADAPTER_NAME,
        adapter_title=AGG_ADAPTER_TITLE,
        adapter_name_raw=f"{AGG_ADAPTER_NAME}_adapter",
        adapter_prefix="specific_data.data",
        all_field="specific_data",
        raw_fields=raw["generic"],
        details=True,
    )

    for raw_name, raw_fields in raw["specific"].items():
        # raw_name = aws_adapter

        prefix = f"adapters_data.{raw_name}"
        # prefix = adapters_data.aws_adapter

        name = strip_right(obj=raw_name, fix="_adapter")
        # name = aws

        title = " ".join(name.split("_")).title()

        fields = parse_schemas(
            adapter_name_raw=raw_name,
            adapter_name=name,
            adapter_prefix=prefix,
            adapter_title=title,
            all_field=prefix,
            raw_fields=raw_fields,
        )
        parsed[name] = fields

    return parsed


def is_complex(field: dict) -> bool:
    """Determine if a field is complex from its schema."""
    field_type = field["type"]
    field_items_type = field.get("items", {}).get("type")
    if field_type == "array" and field_items_type == "array":
        return True
    return False


def is_root(name: str, names: List[str]) -> bool:
    """Determine if a field is a root field."""
    dots = name.split(".")
    return not (len(dots) > 1 and dots[0] in names)


def parse_complex(field: dict):
    """Pass."""
    field["is_complex"] = is_complex(field=field)
    if field["is_complex"]:
        col_title = field["column_title"]
        col_name = field["column_name"]
        name_base = field["name_base"]
        prefix = field["adapter_prefix"]
        field["sub_fields"] = sub_fields = []
        items = field["items"].pop("items")

        field_names = [f["name"] for f in items]

        for sub_field in items:
            sub_title = sub_field["title"]
            sub_name = sub_field["name"]
            sub_name_base = f"{name_base}.{sub_name}"
            sub_name_qual = f"{prefix}.{sub_name_base}"

            sub_field["name_base"] = sub_name_base
            sub_field["name_qual"] = sub_name_qual
            sub_field["is_root"] = is_root(name=sub_name, names=field_names)
            sub_field["is_list"] = sub_field["type"] == "array"
            sub_field["parent"] = field["name_qual"]
            sub_field["adapter_name"] = field["adapter_name"]
            sub_field["adapter_name_raw"] = field["adapter_name_raw"]
            sub_field["adapter_prefix"] = field["adapter_prefix"]
            sub_field["adapter_title"] = field["adapter_title"]
            sub_field["column_title"] = f"{col_title}: {sub_title}"
            sub_field["column_name"] = f"{col_name}.{sub_name}"
            type_map = OperatorTypeMaps.get(field=sub_field)
            sub_field["type_norm"] = type_map.name
            sub_field["selectable"] = True
            parse_complex(field=sub_field)
            sub_fields.append(sub_field)


def parse_schemas(
    adapter_name_raw: str,
    adapter_name: str,
    adapter_prefix: str,
    adapter_title: str,
    all_field: str,
    raw_fields: List[dict],
    details: bool = False,
) -> List[dict]:
    """Parse field schemas for an adapter."""
    fields = []

    fields.append(
        {
            "adapter_name_raw": adapter_name_raw,
            "adapter_name": adapter_name,
            "adapter_title": adapter_title,
            "adapter_prefix": adapter_prefix,
            "column_name": f"{adapter_name}:{ALL_NAME}",
            "column_title": f"All {adapter_title} Data",
            "sub_fields": [],
            "is_complex": True,
            "is_list": True,
            "is_root": False,
            "parent": "root",
            "name": ALL_NAME,
            "name_base": ALL_NAME,
            "name_qual": all_field,
            "title": "All Adapter Specific Data",
            "type": "array",
            "type_norm": "array_object_object",
            "selectable": True,
        }
    )

    if details:
        fields += [
            {
                "adapter_name_raw": adapter_name_raw,
                "adapter_name": adapter_name,
                "adapter_title": adapter_title,
                "adapter_prefix": adapter_prefix,
                "column_name": f"{adapter_name}:unique_adapter_names_details",
                "column_title": "Unique Adapter Names Details Index",
                "sub_fields": [],
                "is_complex": False,
                "is_list": True,
                "is_root": True,
                "parent": "root",
                "name": "unique_adapter_names_details",
                "name_base": "unique_adapter_names_details",
                "name_qual": "unique_adapter_names_details",
                "title": "Unique Adapter Names Details Index",
                "type": "array",
                "type_norm": "array_string",
                "selectable": False,
            },
            {
                "adapter_name_raw": adapter_name_raw,
                "adapter_name": adapter_name,
                "adapter_title": adapter_title,
                "adapter_prefix": adapter_prefix,
                "column_name": f"{adapter_name}:meta_data.client_used",
                "column_title": "Adapter Connection Details Index",
                "sub_fields": [],
                "is_complex": False,
                "is_list": True,
                "is_root": True,
                "parent": "root",
                "name": "meta_data.client_used",
                "name_base": "meta_data.client_used",
                "name_qual": "meta_data.client_used",
                "title": "Adapter Connection Details Index",
                "type": "array",
                "type_norm": "array_string",
                "selectable": False,
            },
        ]

    field_names = [
        strip_left(obj=f["name"], fix=adapter_prefix).strip(".") for f in raw_fields
    ]

    for field in raw_fields:
        title = field["title"]
        name_base = strip_left(obj=field["name"], fix=adapter_prefix).strip(".")
        field["adapter_name"] = adapter_name
        field["adapter_title"] = adapter_title
        field["adapter_prefix"] = adapter_prefix
        field["adapter_name_raw"] = adapter_name_raw
        field["name_base"] = name_base
        field["name_qual"] = field["name"]
        field["is_root"] = is_root(name=name_base, names=field_names)
        field["is_list"] = field["type"] == "array"
        field["parent"] = "root"
        field["column_title"] = f"{adapter_title}: {title}"
        field["column_name"] = f"{adapter_name}:{name_base}"
        type_map = OperatorTypeMaps.get(field=field)
        field["type_norm"] = type_map.name
        field["selectable"] = True
        parse_complex(field=field)
        fields.append(field)
        if details:
            field_details = copy.deepcopy(field)
            field_details["name"] += "_details"
            field_details["name_base"] += "_details"
            field_details["name_qual"] += "_details"
            field_details["column_title"] += " Details"
            field_details["column_name"] += "_details"
            field_details["selectable"] = False
            fields.append(field_details)

    return fields


# def get_type_norm(field: dict) -> str:
#     """Get the normalized type of a field."""
#     ftype = field["type"]
#     ffmt = field.get("format", "")
#     fitype = field.get("items", {}).get("type", "")
#     fifmt = field.get("items", {}).get("format", "")
#     check = (ftype, ffmt, fitype, fifmt)

#     for norm_map, norm_type in NORM_TYPE_MAP:
#         if check == norm_map:
#             return norm_type

#     name = field["name"]
#     check = dict(zip(("type", "format", "items.type", "items.format"), check))
#     raise ApiError(f"Unmapped normalized type: {name}: {check}")
