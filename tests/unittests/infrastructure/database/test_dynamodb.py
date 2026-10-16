# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.

"""DynamoDB adapter behavior against Moto and numeric conversion tests."""

from collections.abc import AsyncIterator
from decimal import Decimal

import aioboto3
import pytest
import pytest_asyncio
from botocore.exceptions import ClientError

from recnavi.exceptions.exceptions import ClientConflictError
from recnavi.infrastructure.database.dynamodb import DynamoDb
from recnavi.infrastructure.database.dynamodb import (
    _convert_from_dynamodb_format,
)
from recnavi.infrastructure.database.dynamodb import (
    _convert_to_dynamodb_format,
)


TABLE = "it_projects"
INDEX = "groupId-createdAt-index"


@pytest_asyncio.fixture(scope="module")
async def dynamodb_table(
    mock_aws_session: aioboto3.Session,
) -> AsyncIterator[str]:
    async with mock_aws_session.resource("dynamodb") as resource:
        await resource.create_table(
            TableName=TABLE,
            KeySchema=[{"AttributeName": "projectId", "KeyType": "HASH"}],
            AttributeDefinitions=[
                {"AttributeName": name, "AttributeType": "S"}
                for name in ("projectId", "groupId", "createdAt")
            ],
            GlobalSecondaryIndexes=[
                {
                    "IndexName": INDEX,
                    "KeySchema": [
                        {"AttributeName": "groupId", "KeyType": "HASH"},
                        {"AttributeName": "createdAt", "KeyType": "RANGE"},
                    ],
                    "Projection": {"ProjectionType": "ALL"},
                },
            ],
            BillingMode="PAY_PER_REQUEST",
        )
    try:
        yield TABLE
    finally:
        async with mock_aws_session.client("dynamodb") as client:
            await client.delete_table(TableName=TABLE)


@pytest_asyncio.fixture
async def database(
    dynamodb_table,
    mock_aws_session: aioboto3.Session,
) -> AsyncIterator[DynamoDb]:
    database = DynamoDb(table_name=dynamodb_table)
    database.session = mock_aws_session
    yield database
    async with mock_aws_session.resource("dynamodb") as resource:
        table = await resource.Table(dynamodb_table)
        response = await table.scan()
        for item in response["Items"]:
            await table.delete_item(Key={"projectId": item["projectId"]})


async def seed_projects(database: DynamoDb) -> None:
    for number in range(3):
        await database.put_item(
            {
                "projectId": f"p{number}",
                "groupId": "group-1",
                "createdAt": f"2026-01-0{number + 1}",
                "isActive": number != 1,
                "category": "recording" if number != 2 else "other",
                "version": number,
            },
        )
    await database.put_item(
        {
            "projectId": "outsider",
            "groupId": "group-2",
            "createdAt": "2026-01-01",
        },
    )


@pytest.mark.asyncio
async def test_put_and_get_preserve_nested_values(database):
    item = {
        "projectId": "p1",
        "version": 2,
        "rating": 4.5,
        "isActive": True,
        "profile": {"scores": [1, 2.5], "label": "test"},
    }
    await database.put_item(item)
    result = await database.get_item({"projectId": "p1"})

    assert result == item
    assert type(result["version"]) is int
    assert type(result["rating"]) is float
    assert result["isActive"] is True
    async with database.session.resource(
        "dynamodb",
    ) as resource:
        table = await resource.Table(TABLE)
        stored = (await table.get_item(Key={"projectId": "p1"}))["Item"]
        assert stored["rating"] == Decimal("4.5")
        assert isinstance(stored["rating"], Decimal)


@pytest.mark.asyncio
async def test_missing_item_returns_none(database):
    assert await database.get_item({"projectId": "missing"}) is None


@pytest.mark.asyncio
async def test_delete_preserves_other_items(database):
    await database.put_item({"projectId": "delete"})
    await database.put_item({"projectId": "keep"})
    await database.delete_item({"projectId": "delete"})
    assert await database.get_item({"projectId": "delete"}) is None
    assert await database.get_item({"projectId": "keep"}) == {
        "projectId": "keep",
    }


@pytest.mark.asyncio
async def test_conditional_put_updates_only_matching_version(database):
    await database.put_item({"projectId": "p1", "version": 1})
    await database.put_item(
        {"projectId": "p1", "version": 2},
        condition_expression="version = :expected",
        expression_attribute_values={":expected": 1},
    )
    with pytest.raises(ClientConflictError):
        await database.put_item(
            {"projectId": "p1", "version": 3},
            condition_expression="version = :expected",
            expression_attribute_values={":expected": 1},
        )
    assert await database.get_item({"projectId": "p1"}) == {
        "projectId": "p1",
        "version": 2,
    }


@pytest.mark.asyncio
@pytest.mark.parametrize("version", [None, 0, 4])
async def test_recording_condition_updates_legacy_and_matching_versions(
    database,
    version,
):
    """Execute the exact recording condition against Moto, including legacy data."""
    original = {"projectId": "p1"}
    if version is not None:
        original["version"] = version
    await database.put_item(original)
    updated = {"projectId": "p1", "version": (version or 0) + 1}
    condition = "attribute_not_exists(version) OR version = :previous_version"
    await database.put_item(
        updated,
        condition_expression=condition,
        expression_attribute_values={":previous_version": version or 0},
    )
    assert await database.get_item({"projectId": "p1"}) == updated
    with pytest.raises(ClientConflictError):
        await database.put_item(
            original,
            condition_expression=condition,
            expression_attribute_values={":previous_version": version or 0},
        )
    assert await database.get_item({"projectId": "p1"}) == updated


@pytest.mark.asyncio
async def test_scene_update_preserves_other_scenes_and_top_level_fields(
    database,
):
    """Update a nested scene using placeholders and return the complete saved item."""
    await database.put_item(
        {"projectId": "p1", "scenes": [{"sceneId": "s1"}, {"sceneId": "s2"}]},
    )
    result = await database.update_item(
        key={"projectId": "p1"},
        update_expression="SET scenes[1].#status = :status, scenes[1].videoKey = :key, updatedAt = :now",
        condition_expression="scenes[1].sceneId = :sceneId",
        expression_attribute_names={"#status": "status"},
        expression_attribute_values={
            ":status": "pending",
            ":key": "video.mp4",
            ":now": "now",
            ":sceneId": "s2",
        },
    )
    assert result == {
        "projectId": "p1",
        "scenes": [
            {"sceneId": "s1"},
            {"sceneId": "s2", "status": "pending", "videoKey": "video.mp4"},
        ],
        "updatedAt": "now",
    }
    assert await database.get_item({"projectId": "p1"}) == result


@pytest.mark.asyncio
async def test_update_returns_persisted_item_with_native_numbers(database):
    await database.put_item({"projectId": "p1", "version": 1, "label": "keep"})
    result = await database.update_item(
        key={"projectId": "p1"},
        update_expression="SET #v = :next, rating = :rating",
        condition_expression="#v = :expected",
        expression_attribute_names={"#v": "version"},
        expression_attribute_values={
            ":next": 2,
            ":expected": 1,
            ":rating": 4.5,
        },
    )
    assert result == {
        "projectId": "p1",
        "version": 2,
        "label": "keep",
        "rating": 4.5,
    }
    assert type(result["version"]) is int
    assert type(result["rating"]) is float
    assert await database.get_item({"projectId": "p1"}) == result


@pytest.mark.asyncio
async def test_rejected_update_keeps_stored_item(database):
    original = {"projectId": "p1", "version": 2}
    await database.put_item(original)
    with pytest.raises(ClientConflictError):
        await database.update_item(
            key={"projectId": "p1"},
            update_expression="SET #v = :next",
            condition_expression="#v = :expected",
            expression_attribute_names={"#v": "version"},
            expression_attribute_values={":next": 3, ":expected": 1},
        )
    assert await database.get_item({"projectId": "p1"}) == original


@pytest.mark.asyncio
async def test_query_primary_key_excludes_other_items(database):
    await seed_projects(database)
    result = await database.query(key_condition={"projectId": "p1"})
    assert [item["projectId"] for item in result.items] == ["p1"]
    assert result.last_evaluated_key is None
    assert type(result.items[0]["version"]) is int


@pytest.mark.asyncio
async def test_query_index_applies_all_filters(database):
    await seed_projects(database)
    result = await database.query(
        key_condition={"groupId": "group-1"},
        index=INDEX,
        filter_expression={"isActive": True, "category": "recording"},
    )
    assert [item["projectId"] for item in result.items] == ["p0"]


@pytest.mark.asyncio
async def test_query_pagination_returns_each_matching_item_once(database):
    await seed_projects(database)
    first = await database.query(
        key_condition={"groupId": "group-1"},
        index=INDEX,
        limit=1,
    )
    assert len(first.items) == 1
    assert first.last_evaluated_key is not None
    items = list(first.items)
    start_key = first.last_evaluated_key
    while start_key:
        page = await database.query(
            key_condition={"groupId": "group-1"},
            index=INDEX,
            limit=1,
            exclusive_start_key=start_key,
        )
        items.extend(page.items)
        start_key = page.last_evaluated_key
    assert [item["projectId"] for item in items] == ["p0", "p1", "p2"]


@pytest.mark.asyncio
async def test_scan_applies_all_filters(database):
    await seed_projects(database)
    result = await database.scan(
        filter_expression={"groupId": "group-1", "isActive": True},
    )
    assert {item["projectId"] for item in result.items} == {"p0", "p2"}


@pytest.mark.asyncio
async def test_scan_pagination_returns_every_item_once(database):
    await seed_projects(database)
    first = await database.scan(limit=1)
    assert len(first.items) == 1
    assert first.last_evaluated_key is not None
    items = list(first.items)
    start_key = first.last_evaluated_key
    while start_key:
        page = await database.scan(limit=1, exclusive_start_key=start_key)
        items.extend(page.items)
        start_key = page.last_evaluated_key
    assert sorted(item["projectId"] for item in items) == [
        "outsider",
        "p0",
        "p1",
        "p2",
    ]


@pytest.mark.asyncio
@pytest.mark.parametrize("operation", ["put", "update", "get"])
async def test_missing_table_propagates_resource_error(
    dynamodb_table,
    mock_aws_session,
    operation,
):
    missing = DynamoDb(table_name="it_missing")
    missing.session = mock_aws_session
    with pytest.raises(ClientError) as exc_info:
        if operation == "put":
            await missing.put_item({"projectId": "p1"})
        elif operation == "update":
            await missing.update_item(
                key={"projectId": "p1"},
                update_expression="SET n = :n",
                expression_attribute_values={":n": 1},
            )
        else:
            await missing.get_item({"projectId": "p1"})
    assert (
        exc_info.value.response["Error"]["Code"] == "ResourceNotFoundException"
    )


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
