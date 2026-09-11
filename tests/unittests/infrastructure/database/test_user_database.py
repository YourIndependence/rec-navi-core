# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.

"""Tests for UserDatabase DynamoDB implementation."""

import pytest
from moto import mock_aws

from recnavi.infrastructure.database.user_database import UserDatabase


@pytest.fixture
def dynamodb_table():
    """Create a mock DynamoDB table for testing."""
    with mock_aws():
        import boto3

        dynamodb = boto3.resource("dynamodb", region_name="ap-northeast-1")

        table = dynamodb.create_table(
            TableName="test-users",
            KeySchema=[{"AttributeName": "userId", "KeyType": "HASH"}],
            AttributeDefinitions=[
                {"AttributeName": "userId", "AttributeType": "S"},
            ],
            BillingMode="PAY_PER_REQUEST",
        )

        yield table


@pytest.mark.asyncio
async def test_get_item_returns_user_when_exists(dynamodb_table):
    """Test get_item returns user data when user exists."""
    user_id = "user-123"
    user_data = {
        "userId": user_id,
        "userName": "Test User",
        "role": "admin",
        "groupId": "group-456",
    }

    dynamodb_table.put_item(Item=user_data)

    user_db = UserDatabase(table_name="test-users")
    result = await user_db.get_item(key={"userId": user_id})

    assert result is not None
    assert result["userId"] == user_id
    assert result["userName"] == "Test User"
    assert result["role"] == "admin"
    assert result["groupId"] == "group-456"


@pytest.mark.asyncio
async def test_get_item_returns_none_when_not_exists(dynamodb_table):
    """Test get_item returns None when user does not exist."""
    user_db = UserDatabase(table_name="test-users")
    result = await user_db.get_item(key={"userId": "nonexistent"})

    assert result is None


@pytest.mark.asyncio
async def test_put_item_stores_user_data(dynamodb_table):
    """Test put_item successfully stores user data."""
    user_data = {
        "userId": "user-789",
        "userName": "New User",
        "role": "staff",
        "groupId": "group-101",
    }

    user_db = UserDatabase(table_name="test-users")
    await user_db.put_item(item=user_data)

    response = dynamodb_table.get_item(Key={"userId": "user-789"})
    assert "Item" in response
    assert response["Item"]["userName"] == "New User"
    assert response["Item"]["role"] == "staff"


@pytest.mark.asyncio
async def test_delete_item_removes_user(dynamodb_table):
    """Test delete_item removes user from table."""
    user_data = {
        "userId": "user-delete",
        "userName": "Delete Me",
        "role": "owner",
        "groupId": "group-999",
    }

    dynamodb_table.put_item(Item=user_data)

    user_db = UserDatabase(table_name="test-users")
    await user_db.delete_item(key={"userId": "user-delete"})

    response = dynamodb_table.get_item(Key={"userId": "user-delete"})
    assert "Item" not in response
