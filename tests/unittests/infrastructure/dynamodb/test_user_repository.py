# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.

"""Unit tests for the DynamoDB user repository."""

import boto3
import pytest
from moto import mock_aws

from recnavi.core.repositories.user_repository import BaseUserRepository
from recnavi.core.types.group_user import UserRole
from recnavi.infrastructure.dynamodb.user_repository import (
    DynamoDbUserRepository,
)


TABLE_NAME = "recnavi-test-users"

OWNER = {
    "userId": "7f1c0f2e",
    "groupId": "grp_sushi_taro",
    "role": "owner",
    "userName": "Koki Ueno",
    "createdAt": "2026-09-07T10:00:00Z",
}


def _create_table():
    """Create the users table the way the infrastructure defines it."""
    resource = boto3.resource("dynamodb", region_name="ap-northeast-1")
    return resource.create_table(
        TableName=TABLE_NAME,
        BillingMode="PAY_PER_REQUEST",
        AttributeDefinitions=[
            {"AttributeName": "userId", "AttributeType": "S"},
            {"AttributeName": "groupId", "AttributeType": "S"},
        ],
        KeySchema=[{"AttributeName": "userId", "KeyType": "HASH"}],
        GlobalSecondaryIndexes=[
            {
                "IndexName": "groupId-index",
                "KeySchema": [
                    {"AttributeName": "groupId", "KeyType": "HASH"},
                ],
                "Projection": {"ProjectionType": "ALL"},
            },
        ],
    )


@pytest.mark.asyncio
async def test_gets_a_user_by_id():
    """The record carries the tenant and what the user may do."""
    with mock_aws():
        table = _create_table()
        table.put_item(Item=OWNER)

        user = await DynamoDbUserRepository(table_name=TABLE_NAME).get(
            user_id="7f1c0f2e",
        )

    assert user is not None
    assert user.user_id == "7f1c0f2e"
    assert user.user_name == "Koki Ueno"
    assert user.role is UserRole.OWNER
    assert user.group_id == "grp_sushi_taro"


@pytest.mark.asyncio
async def test_answers_nothing_for_a_user_with_no_record():
    """Signing up in Cognito does not by itself make an account usable."""
    with mock_aws():
        _create_table()

        user = await DynamoDbUserRepository(table_name=TABLE_NAME).get(
            user_id="nobody",
        )

    assert user is None


def test_implements_the_core_abstraction():
    """The application layer only ever sees the abstraction."""
    assert issubclass(DynamoDbUserRepository, BaseUserRepository)
