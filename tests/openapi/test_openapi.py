import json
import os

import jsonschema

import zangar as z
from zangar.compilation import OpenAPI30Compiler


class TestOpenAPI30:
    with open(os.path.join(os.path.dirname(__file__), "2024-10-18")) as fp:
        OPENAPISPEC_30 = json.load(fp)

    @classmethod
    def compile(cls, schema):
        schema_object = OpenAPI30Compiler().compile(schema)
        jsonschema.validate(
            {
                "openapi": "3.0.3",
                "info": {
                    "title": "Test",
                    "version": "1.0.0",
                },
                "paths": {},
                "components": {
                    "schemas": {
                        "Test": schema_object,
                    }
                },
            },
            cls.OPENAPISPEC_30,
        )
        return schema_object

    def test_nullable(self):
        assert self.compile(z.int() | z.none()) == {
            "type": "integer",
            "nullable": True,
        }

    def test_datetime(self):
        assert self.compile(z.datetime()) == {
            "type": "string",
            "format": "date-time",
        }

    def test_object_type(self):
        assert self.compile(
            z.object(
                {
                    "name": z.str(),
                }
            )
        ) == {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                }
            },
            "required": ["name"],
        }

    def test_object_property_required_and_alias(self):
        assert self.compile(
            z.object(
                {
                    "name": z.field(z.str(), alias="name_alias").optional(),
                },
            )
        ) == {
            "type": "object",
            "properties": {
                "name_alias": {
                    "type": "string",
                }
            },
        }

    def test_union(self):
        assert self.compile(z.str() | z.int()) == {
            "anyOf": [
                {
                    "type": "string",
                },
                {
                    "type": "integer",
                },
            ],
        }
        assert self.compile(z.str() | z.int() | z.none()) == {
            "anyOf": [
                {
                    "type": "string",
                },
                {
                    "type": "integer",
                },
            ],
            "nullable": True,
        }

    def test_min_max_length(self):
        assert self.compile(z.str().min(1).max(10)) == {
            "type": "string",
            "minLength": 1,
            "maxLength": 10,
        }

    def test_minim_maxim(self):
        assert self.compile(z.int().gte(1).lte(10)) == {
            "type": "integer",
            "minimum": 1,
            "maximum": 10,
        }
        assert self.compile(z.int().gt(1).lt(10)) == {
            "type": "integer",
            "minimum": 1,
            "exclusiveMinimum": True,
            "maximum": 10,
            "exclusiveMaximum": True,
        }

    def test_any_type(self):
        assert self.compile(z.any()) == {
            "nullable": True,
        }

    def test_to_type(self):
        assert self.compile(z.to.int()) == {
            "type": "integer",
        }

    def test_raw_schema(self):
        assert self.compile(z.transform(int)) == {}

    def test_array(self):
        assert self.compile(z.list()) == {
            "type": "array",
            "items": {
                "nullable": True,
            },
        }
        assert self.compile(z.list(z.int())) == {
            "type": "array",
            "items": {
                "type": "integer",
            },
        }

    def test_none(self):
        assert self.compile(z.none()) == {"enum": [None]}

    def test_default(self):
        assert self.compile(
            z.object(
                {
                    "a1": z.field(z.str()).optional(default="test"),
                    "a2": z.field(z.str()).optional(default=lambda: "test"),
                }
            )
        ) == {
            "type": "object",
            "properties": {
                "a1": {
                    "type": "string",
                    "default": "test",
                },
                "a2": {
                    "type": "string",
                },
            },
        }

    def test_dataclass(self):
        from dataclasses import dataclass, field

        @dataclass
        class C:
            a: str = field(default="test")
            b: str = field(default_factory=lambda: "test")

        assert self.compile(z.dataclass(C)) == {
            "type": "object",
            "properties": {
                "a": {
                    "type": "string",
                    "default": "test",
                },
                "b": {
                    "type": "string",
                },
            },
        }
