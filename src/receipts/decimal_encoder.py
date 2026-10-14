from decimal import Decimal
from typing import Any

import simplejson as json
from sqlalchemy import JSON
from sqlalchemy.types import TypeDecorator

_DECIMAL_KEY = "__decimal__"


def encode_decimals(value: Any) -> Any:
    if isinstance(value, Decimal):
        return {_DECIMAL_KEY: str(value)}
    if isinstance(value, dict):
        return {key: encode_decimals(item) for key, item in value.items()}
    if isinstance(value, list):
        return [encode_decimals(item) for item in value]
    return value


def decode_decimals(value: Any) -> Any:
    if isinstance(value, dict):
        if set(value) == {_DECIMAL_KEY}:
            return Decimal(value[_DECIMAL_KEY])
        return {key: decode_decimals(item) for key, item in value.items()}
    if isinstance(value, list):
        return [decode_decimals(item) for item in value]
    return value


class DecimalJSON(TypeDecorator):
    impl = JSON
    cache_ok = True

    def process_bind_param(self, value, dialect):
        return encode_decimals(value) if value is not None else None

    def process_result_value(self, value, dialect):
        return decode_decimals(value) if value is not None else None


class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, Decimal):
            return str(o)
        return super().default(o)

from sqlalchemy.ext.declarative import DeclarativeMeta


def new_alchemy_encoder():
    _visited_objs = []

    class AlchemyEncoder(json.JSONEncoder):
        def default(self, o):
            if isinstance(o.__class__, DeclarativeMeta):
                # don't re-visit self
                if o in _visited_objs:
                    return None
                _visited_objs.append(o)

                fields = {}
                for field in [x for x in dir(o) if not x.startswith('_') and x != 'metadata']:
                    fields[field] = o.__getattribute__(field)
                return fields

            return json.JSONEncoder.default(self, o)

    return AlchemyEncoder