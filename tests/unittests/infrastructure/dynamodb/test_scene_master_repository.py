# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.

"""Unit tests for the DynamoDB scene master repository."""

import boto3
import pytest
from moto import mock_aws

from recnavi.core.repositories.scene_master_repository import (
    BaseSceneMasterRepository,
)
from recnavi.infrastructure.dynamodb.scene_master_repository import (
    DynamoDbSceneMasterRepository,
)


TABLE_NAME = "recnavi-test-scenes"

SHOP_GAIKAN = {
    "scenePrincipal": "shop_gaikan",
    "title": "Shop exterior",
    "thumbnailUri": "assets/scenes/shop_gaikan/example.jpg",
    "guideUri": "assets/scenes/shop_gaikan/guide.png",
    "maxDurationSeconds": 5,
}
MAIN_DISH = {
    "scenePrincipal": "main_dish",
    "title": "Signature dish",
    "thumbnailUri": "assets/scenes/main_dish/example.jpg",
    "guideUri": "assets/scenes/main_dish/guide.png",
    "maxDurationSeconds": 3,
}


def _create_table():
    """Create the scenes table the way the infrastructure defines it."""
    resource = boto3.resource("dynamodb", region_name="ap-northeast-1")
    return resource.create_table(
        TableName=TABLE_NAME,
        BillingMode="PAY_PER_REQUEST",
        AttributeDefinitions=[
            {"AttributeName": "scenePrincipal", "AttributeType": "S"},
        ],
        KeySchema=[
            {"AttributeName": "scenePrincipal", "KeyType": "HASH"},
        ],
    )


@pytest.mark.asyncio
async def test_lists_every_stored_master():
    """Every row in the table comes back."""
    with mock_aws():
        table = _create_table()
        table.put_item(Item=SHOP_GAIKAN)
        table.put_item(Item=MAIN_DISH)

        masters = await DynamoDbSceneMasterRepository(
            table_name=TABLE_NAME,
        ).list_all()

    by_principal = {m.scene_principal: m for m in masters}
    assert set(by_principal) == {"shop_gaikan", "main_dish"}
    assert by_principal["shop_gaikan"].title == "Shop exterior"
    assert by_principal["shop_gaikan"].max_duration_seconds == 5
    assert (
        by_principal["shop_gaikan"].thumbnail_uri
        == "assets/scenes/shop_gaikan/example.jpg"
    )
    assert (
        by_principal["main_dish"].guide_uri
        == "assets/scenes/main_dish/guide.png"
    )


@pytest.mark.asyncio
async def test_returns_nothing_from_an_empty_table():
    """An empty table is not an error."""
    with mock_aws():
        _create_table()

        masters = await DynamoDbSceneMasterRepository(
            table_name=TABLE_NAME,
        ).list_all()

    assert masters == []


@pytest.mark.asyncio
async def test_reads_beyond_a_single_scan_page():
    """A scan that stops early is continued, not silently truncated."""
    with mock_aws():
        table = _create_table()
        for index in range(30):
            table.put_item(
                Item={**SHOP_GAIKAN, "scenePrincipal": f"scene_{index:02d}"},
            )

        repository = DynamoDbSceneMasterRepository(table_name=TABLE_NAME)
        masters = await repository.list_all()

    assert len(masters) == 30


@pytest.mark.asyncio
async def test_gets_one_master_by_principal():
    """A single master is fetched by key, not by scanning."""
    with mock_aws():
        table = _create_table()
        table.put_item(Item=SHOP_GAIKAN)
        table.put_item(Item=MAIN_DISH)

        master = await DynamoDbSceneMasterRepository(
            table_name=TABLE_NAME,
        ).get(scene_principal="main_dish")

    assert master is not None
    assert master.title == "Signature dish"
    assert master.guide_uri == "assets/scenes/main_dish/guide.png"


@pytest.mark.asyncio
async def test_answers_nothing_for_an_unknown_principal():
    """An unknown principal is not an error the caller has to catch."""
    with mock_aws():
        _create_table()

        master = await DynamoDbSceneMasterRepository(
            table_name=TABLE_NAME,
        ).get(scene_principal="nowhere")

    assert master is None


def test_implements_the_core_abstraction():
    """The application layer only ever sees the abstraction."""
    assert issubclass(DynamoDbSceneMasterRepository, BaseSceneMasterRepository)
