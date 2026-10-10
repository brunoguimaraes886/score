from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from starlette.datastructures import QueryParams

from errors import InvalidSchema
from utils.schema_handler import SchemaCache, SchemaHandler


@pytest.mark.parametrize("payload", [{"nested": [{"name": "\u0000"}]}, {"\ud800": "value"}, {"name": "\udfff"}])
def test_invalid_nested_text_never_reaches_resource(monkeypatch, payload):
    monkeypatch.setattr(SchemaCache, "get_schema", lambda name: {})
    resource = Mock(__name__="resource")
    wrapped = SchemaHandler.validate("unused.json")(resource)
    with pytest.raises(InvalidSchema) as error:
        wrapped(payload=payload)
    assert (error.value.http_status, error.value.code) == (400, "QIT000001")
    resource.assert_not_called()


def test_query_text_is_checked_before_resource(monkeypatch):
    monkeypatch.setattr(SchemaCache, "get_schema", lambda name: {})
    resource = Mock(__name__="resource")
    wrapped = SchemaHandler.validate_query_params("unused.json")(resource)
    with pytest.raises(InvalidSchema):
        wrapped(request=SimpleNamespace(query_params=QueryParams({"name": "\u0000"})))
    resource.assert_not_called()
    request = SimpleNamespace(query_params=QueryParams({"name": "José D'Ávila 🏦"}))
    wrapped(request=request)
    resource.assert_called_once_with(request=request)
