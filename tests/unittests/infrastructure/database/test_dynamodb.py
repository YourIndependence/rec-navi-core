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

    items, last_evaluated_key = await database.query(
        key_condition={"KeyConditionExpression": "userId = :user_id"},
        index="group-index",
    )

    assert items == [{"userId": "user-123"}]
    assert last_evaluated_key is None
    assert table.query_kwargs == {
        "KeyConditionExpression": "userId = :user_id",
        "IndexName": "group-index",
    }


@pytest.mark.asyncio
async def test_query_passes_filter_expression_to_dynamodb():
    """Test query converts equality filters to a DynamoDB condition."""
    table = MockDynamoTable()
    resource = MockDynamoResource(table)
    database = DynamoDb(table_name="users")
    database.session = MockDynamoSession(resource)

    await database.query(
        key_condition={"KeyConditionExpression": "userId = :user_id"},
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


@pytest.mark.asyncio
async def test_put_item_with_condition_passes_expression_to_dynamodb():
    """Test put_item passes condition expression to DynamoDB."""

    class MockTableWithCondition:
        def __init__(self) -> None:
            self.put_item_kwargs: dict[str, object] | None = None

        async def put_item(self, **kwargs: object) -> None:
            self.put_item_kwargs = kwargs

    class MockResourceWithCondition:
        def __init__(self, table: MockTableWithCondition) -> None:
            self.table = table

        async def __aenter__(self) -> "MockResourceWithCondition":
            return self

        async def __aexit__(self, *args: object) -> None:
            return None

        async def Table(self, _table_name: str) -> MockTableWithCondition:  # noqa: N802
            return self.table

    class MockSessionWithCondition:
        def __init__(self, resource: MockResourceWithCondition) -> None:
            self.dynamodb_resource = resource

        def resource(self, _service_name: str) -> MockResourceWithCondition:
            return self.dynamodb_resource

    table = MockTableWithCondition()
    resource = MockResourceWithCondition(table)
    database = DynamoDb(table_name="projects")
    database.session = MockSessionWithCondition(resource)

    await database.put_item(
        item={"projectId": "proj-123", "version": 2},
        condition_expression="version = :expected_version",
        expression_attribute_values={":expected_version": 1},
    )

    assert table.put_item_kwargs is not None
    assert (
        table.put_item_kwargs["ConditionExpression"]
        == "version = :expected_version"
    )
    assert table.put_item_kwargs["ExpressionAttributeValues"] == {
        ":expected_version": 1,
    }


@pytest.mark.asyncio
async def test_put_item_raises_conflict_when_condition_check_fails():
    """Test put_item raises ClientConflictError on ConditionalCheckFailedException."""
    from botocore.exceptions import ClientError

    class MockTableThatFailsCondition:
        async def put_item(self, **kwargs: object) -> None:
            raise ClientError(
                error_response={
                    "Error": {
                        "Code": "ConditionalCheckFailedException",
                        "Message": "The conditional request failed",
                    },
                },
                operation_name="PutItem",
            )

    class MockResourceWithFailingTable:
        def __init__(self, table: MockTableThatFailsCondition) -> None:
            self.table = table

        async def __aenter__(self) -> "MockResourceWithFailingTable":
            return self

        async def __aexit__(self, *args: object) -> None:
            return None

        async def Table(self, _table_name: str) -> MockTableThatFailsCondition:  # noqa: N802
            return self.table

    class MockSessionWithFailingTable:
        def __init__(self, resource: MockResourceWithFailingTable) -> None:
            self.dynamodb_resource = resource

        def resource(self, _service_name: str) -> MockResourceWithFailingTable:
            return self.dynamodb_resource

    table = MockTableThatFailsCondition()
    resource = MockResourceWithFailingTable(table)
    database = DynamoDb(table_name="projects")
    database.session = MockSessionWithFailingTable(resource)

    with pytest.raises(ClientConflictError) as exc_info:
        await database.put_item(
            item={"projectId": "proj-123", "version": 3},
            condition_expression="version = :expected_version",
            expression_attribute_values={":expected_version": 1},
        )

    assert "ConditionalCheckFailedException" in str(exc_info.value)
