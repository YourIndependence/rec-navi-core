# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.

"""Tests for DynamoDb Decimal conversion logic."""

from decimal import Decimal

import pytest
from botocore.exceptions import ClientError

from recnavi.exceptions.exceptions import ClientConflictError
from recnavi.infrastructure.database.dynamodb import DynamoDb
from recnavi.infrastructure.database.dynamodb import (
    _convert_from_dynamodb_format,
)
from recnavi.infrastructure.database.dynamodb import (
    _convert_to_dynamodb_format,
)


class MockDynamoTable:
    """Minimal async DynamoDB table fake for query tests."""

    def __init__(self) -> None:
        self.query_kwargs: dict[str, object] | None = None
        self.scan_kwargs: dict[str, object] | None = None

    async def query(self, **kwargs: object) -> dict[str, list[dict[str, str]]]:
        self.query_kwargs = kwargs
        return {"Items": [{"userId": "user-123"}]}

    async def scan(self, **kwargs: object) -> dict[str, list[dict[str, str]]]:
        self.scan_kwargs = kwargs
        return {"Items": [{"userId": "user-123"}]}


class MockDynamoResource:
    """Minimal async DynamoDB resource fake for query tests."""

    def __init__(self, table: MockDynamoTable) -> None:
        self.table = table

    async def __aenter__(self) -> "MockDynamoResource":
        return self

    async def __aexit__(self, *args: object) -> None:
        return None

    async def Table(self, _table_name: str) -> MockDynamoTable:  # noqa: N802
        return self.table


class MockDynamoSession:
    """Minimal aioboto3 session fake for query tests."""

    def __init__(self, resource: MockDynamoResource) -> None:
        self.dynamodb_resource = resource

    def resource(self, _service_name: str) -> MockDynamoResource:
        return self.dynamodb_resource


@pytest.mark.asyncio
async def test_query_passes_index_name_to_dynamodb():
    """Test query passes the optional index as DynamoDB IndexName."""
    table = MockDynamoTable()
    resource = MockDynamoResource(table)
    database = DynamoDb(table_name="users")
    database.session = MockDynamoSession(resource)

    result = await database.query(
        key_condition={"userId": "user-123"},
        index="group-index",
    )

    assert result.items == [{"userId": "user-123"}]
    assert result.last_evaluated_key is None
    assert table.query_kwargs is not None
    assert table.query_kwargs["IndexName"] == "group-index"
    expression = table.query_kwargs["KeyConditionExpression"].get_expression()
    assert expression["operator"] == "="
    assert expression["values"][0].name == "userId"
    assert expression["values"][1] == "user-123"


@pytest.mark.asyncio
async def test_query_converts_attribute_key_condition_to_expression():
    """Test query converts attribute equality conditions for DynamoDB."""
    table = MockDynamoTable()
    resource = MockDynamoResource(table)
    database = DynamoDb(table_name="projects")
    database.session = MockDynamoSession(resource)

    await database.query(
        key_condition={"groupId": "group-123"},
        index="GSI1",
    )

    assert table.query_kwargs is not None
    assert "groupId" not in table.query_kwargs
    key_expression = table.query_kwargs["KeyConditionExpression"]
    expression = key_expression.get_expression()
    assert expression["operator"] == "="
    assert expression["values"][0].name == "groupId"
    assert expression["values"][1] == "group-123"
    assert table.query_kwargs["IndexName"] == "GSI1"


@pytest.mark.asyncio
async def test_query_passes_filter_expression_to_dynamodb():
    """Test query converts equality filters to a DynamoDB condition."""
    table = MockDynamoTable()
    resource = MockDynamoResource(table)
    database = DynamoDb(table_name="users")
    database.session = MockDynamoSession(resource)

    await database.query(
        key_condition={"userId": "user-123"},
        filter_expression={"isActive": True},
    )

    assert table.query_kwargs is not None
    filter_expression = table.query_kwargs["FilterExpression"]
    expression = filter_expression.get_expression()
    assert expression["format"] == "{0} {operator} {1}"
    assert expression["operator"] == "="
    assert expression["values"][0].name == "isActive"
    assert expression["values"][1] is True


@pytest.mark.asyncio
async def test_scan_passes_filter_expression_to_dynamodb():
    """Test scan converts equality filters to a DynamoDB condition."""
    table = MockDynamoTable()
    resource = MockDynamoResource(table)
    database = DynamoDb(table_name="users")
    database.session = MockDynamoSession(resource)

    await database.scan(filter_expression={"role": "admin"})

    assert table.scan_kwargs is not None
    filter_expression = table.scan_kwargs["FilterExpression"]
    expression = filter_expression.get_expression()
    assert expression["format"] == "{0} {operator} {1}"
    assert expression["operator"] == "="
    assert expression["values"][0].name == "role"
    assert expression["values"][1] == "admin"


def test_convert_to_dynamodb_converts_int_to_decimal():
    """Test _convert_to_dynamodb_format converts int to Decimal."""
    item = {"userId": "user-123", "age": 25, "score": 100}

    result = _convert_to_dynamodb_format(item)

    assert result["userId"] == "user-123"
    assert isinstance(result["age"], Decimal)
    assert isinstance(result["score"], Decimal)
    assert result["age"] == Decimal("25")
    assert result["score"] == Decimal("100")


def test_convert_to_dynamodb_converts_float_to_decimal():
    """Test _convert_to_dynamodb_format converts float to Decimal."""
    item = {"userId": "user-123", "rating": 4.5, "price": 19.99}

    result = _convert_to_dynamodb_format(item)

    assert result["userId"] == "user-123"
    assert isinstance(result["rating"], Decimal)
    assert isinstance(result["price"], Decimal)
    assert float(result["rating"]) == 4.5
    assert float(result["price"]) == 19.99


def test_convert_to_dynamodb_preserves_strings():
    """Test _convert_to_dynamodb_format preserves string values."""
    item = {"userId": "user-123", "userName": "Test User"}

    result = _convert_to_dynamodb_format(item)

    assert result["userId"] == "user-123"
    assert result["userName"] == "Test User"


def test_convert_to_dynamodb_preserves_booleans():
    """Test _convert_to_dynamodb_format preserves boolean values."""
    item = {"userId": "user-123", "isActive": True, "isDeleted": False}

    result = _convert_to_dynamodb_format(item)

    assert result["isActive"] is True
    assert result["isDeleted"] is False


def test_convert_to_dynamodb_handles_nested_dicts():
    """Test _convert_to_dynamodb_format handles nested dictionaries."""
    item = {
        "userId": "user-123",
        "profile": {"age": 30, "rating": 4.5, "name": "Alice"},
    }

    result = _convert_to_dynamodb_format(item)

    assert result["userId"] == "user-123"
    assert isinstance(result["profile"]["age"], Decimal)
    assert isinstance(result["profile"]["rating"], Decimal)
    assert result["profile"]["name"] == "Alice"


def test_convert_to_dynamodb_handles_lists():
    """Test _convert_to_dynamodb_format handles lists."""
    item = {
        "userId": "user-123",
        "scores": [10, 20, 30],
        "ratings": [4.5, 3.8],
    }

    result = _convert_to_dynamodb_format(item)

    assert result["userId"] == "user-123"
    assert all(isinstance(score, Decimal) for score in result["scores"])
    assert all(isinstance(rating, Decimal) for rating in result["ratings"])


def test_convert_from_dynamodb_converts_decimal_to_int():
    """Test _convert_from_dynamodb_format converts Decimal to int."""
    item = {
        "userId": "user-123",
        "age": Decimal("25"),
        "score": Decimal("100"),
    }

    result = _convert_from_dynamodb_format(item)

    assert result["userId"] == "user-123"
    assert isinstance(result["age"], int)
    assert isinstance(result["score"], int)
    assert result["age"] == 25
    assert result["score"] == 100


def test_convert_from_dynamodb_converts_decimal_to_float():
    """Test _convert_from_dynamodb_format converts Decimal to float."""
    item = {
        "userId": "user-123",
        "rating": Decimal("4.5"),
        "price": Decimal("19.99"),
    }

    result = _convert_from_dynamodb_format(item)

    assert result["userId"] == "user-123"
    assert isinstance(result["rating"], float)
    assert isinstance(result["price"], float)
    assert result["rating"] == 4.5
    assert result["price"] == 19.99


def test_convert_from_dynamodb_preserves_strings():
    """Test _convert_from_dynamodb_format preserves string values."""
    item = {"userId": "user-123", "userName": "Test User"}

    result = _convert_from_dynamodb_format(item)

    assert result["userId"] == "user-123"
    assert result["userName"] == "Test User"


def test_convert_from_dynamodb_handles_nested_dicts():
    """Test _convert_from_dynamodb_format handles nested dictionaries."""
    item = {
        "userId": "user-123",
        "profile": {
            "age": Decimal("30"),
            "rating": Decimal("4.5"),
            "name": "Alice",
        },
    }

    result = _convert_from_dynamodb_format(item)

    assert result["userId"] == "user-123"
    assert isinstance(result["profile"]["age"], int)
    assert isinstance(result["profile"]["rating"], float)
    assert result["profile"]["name"] == "Alice"
    assert result["profile"]["age"] == 30
    assert result["profile"]["rating"] == 4.5


def test_convert_from_dynamodb_handles_lists_with_decimals():
    """Test _convert_from_dynamodb_format handles lists with Decimals."""
    item = {
        "userId": "user-123",
        "scores": [Decimal("10"), Decimal("20"), Decimal("30")],
        "ratings": [Decimal("4.5"), Decimal("3.8")],
    }

    result = _convert_from_dynamodb_format(item)

    assert result["userId"] == "user-123"
    assert all(isinstance(score, int) for score in result["scores"])
    assert all(isinstance(rating, float) for rating in result["ratings"])
    assert result["scores"] == [10, 20, 30]
    assert result["ratings"] == [4.5, 3.8]


def test_convert_roundtrip_preserves_data():
    """Test converting to DynamoDB and back preserves data."""
    original = {
        "userId": "user-123",
        "userName": "Test User",
        "age": 30,
        "rating": 4.5,
        "isActive": True,
        "profile": {"level": 5, "score": 99.9},
    }

    converted_to_ddb = _convert_to_dynamodb_format(original)
    converted_back = _convert_from_dynamodb_format(converted_to_ddb)

    assert converted_back["userId"] == original["userId"]
    assert converted_back["userName"] == original["userName"]
    assert converted_back["age"] == original["age"]
    assert converted_back["rating"] == original["rating"]
    assert converted_back["isActive"] == original["isActive"]
    assert converted_back["profile"]["level"] == original["profile"]["level"]
    assert converted_back["profile"]["score"] == original["profile"]["score"]


class MockWriteTable:
    """Async DynamoDB table fake for put_item/update_item tests."""

    def __init__(self, error_code: str | None = None) -> None:
        self.error_code = error_code
        self.put_kwargs: dict[str, object] | None = None
        self.update_kwargs: dict[str, object] | None = None

    def _raise_if_configured(self) -> None:
        if self.error_code is not None:
            raise ClientError(
                {"Error": {"Code": self.error_code, "Message": "rejected"}},
                "Write",
            )

    async def put_item(self, **kwargs: object) -> dict[str, object]:
        self.put_kwargs = kwargs
        self._raise_if_configured()
        return {}

    async def update_item(self, **kwargs: object) -> dict[str, object]:
        self.update_kwargs = kwargs
        self._raise_if_configured()
        return {"Attributes": {"projectId": "p1", "version": 2}}


def _build_database(table: MockWriteTable) -> DynamoDb:
    database = DynamoDb(table_name="projects")
    database.session = MockDynamoSession(MockDynamoResource(table))
    return database


@pytest.mark.asyncio
async def test_put_item_without_condition_sends_only_item():
    """Test put_item omits condition arguments when none are given."""
    table = MockWriteTable()

    await _build_database(table).put_item({"projectId": "p1"})

    assert table.put_kwargs == {"Item": {"projectId": "p1"}}


@pytest.mark.asyncio
async def test_put_item_passes_condition_to_dynamodb():
    """Test put_item forwards the condition and converted values."""
    table = MockWriteTable()

    await _build_database(table).put_item(
        {"projectId": "p1", "version": 2},
        condition_expression="version = :expected_version",
        expression_attribute_values={":expected_version": 1},
    )

    assert table.put_kwargs is not None
    assert table.put_kwargs["ConditionExpression"] == (
        "version = :expected_version"
    )
    assert table.put_kwargs["ExpressionAttributeValues"] == {
        ":expected_version": Decimal(1),
    }


@pytest.mark.asyncio
async def test_put_item_conditional_failure_raises_conflict():
    """Test ConditionalCheckFailedException becomes ClientConflictError."""
    table = MockWriteTable(error_code="ConditionalCheckFailedException")

    with pytest.raises(ClientConflictError, match="rejected"):
        await _build_database(table).put_item(
            {"projectId": "p1"},
            condition_expression="version = :expected_version",
            expression_attribute_values={":expected_version": 1},
        )


@pytest.mark.asyncio
async def test_put_item_reraises_other_client_errors():
    """Test other DynamoDB errors are not converted."""
    table = MockWriteTable(error_code="ProvisionedThroughputExceeded")

    with pytest.raises(ClientError):
        await _build_database(table).put_item({"projectId": "p1"})


@pytest.mark.asyncio
async def test_update_item_returns_converted_attributes():
    """Test update_item sends expressions and returns the new item."""
    table = MockWriteTable()

    result = await _build_database(table).update_item(
        key={"projectId": "p1"},
        update_expression="SET #s = :s",
        condition_expression="attribute_exists(projectId)",
        expression_attribute_names={"#s": "status"},
        expression_attribute_values={":s": "SUBMITTED"},
    )

    assert result == {"projectId": "p1", "version": 2}
    assert table.update_kwargs == {
        "Key": {"projectId": "p1"},
        "UpdateExpression": "SET #s = :s",
        "ReturnValues": "ALL_NEW",
        "ConditionExpression": "attribute_exists(projectId)",
        "ExpressionAttributeNames": {"#s": "status"},
        "ExpressionAttributeValues": {":s": "SUBMITTED"},
    }


@pytest.mark.asyncio
async def test_update_item_conditional_failure_raises_conflict():
    """Test a failed update condition becomes ClientConflictError."""
    table = MockWriteTable(error_code="ConditionalCheckFailedException")

    with pytest.raises(ClientConflictError):
        await _build_database(table).update_item(
            key={"projectId": "p1"},
            update_expression="SET #s = :s",
            condition_expression="scenes[0].sceneId = :sceneId",
        )
