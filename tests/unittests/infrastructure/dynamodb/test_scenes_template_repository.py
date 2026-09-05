# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.

"""Unit tests for the DynamoDB scenes template repository."""

import boto3
import pytest
from moto import mock_aws

from recnavi.core.repositories.scenes_template_repository import (
    BaseScenesTemplateRepository,
)
from recnavi.infrastructure.dynamodb.scenes_template_repository import (
    DynamoDbScenesTemplateRepository,
)


TABLE_NAME = "recnavi-test-scene-templates"

CAFE = {
    "templateId": "tpl_cafe",
    "title": "Cafe",
    "scenePrincipals": ["shop_gaikan", "main_dish", "main_dish"],
    "thumbnailUri": "assets/templates/tpl_cafe.jpg",
}
HOTEL = {
    "templateId": "tpl_hotel",
    "title": "Hotel",
    "scenePrincipals": ["shop_gaikan", "room"],
    "thumbnailUri": "assets/templates/tpl_hotel.jpg",
}


def _create_table():
    """Create the templates table the way the infrastructure defines it."""
    resource = boto3.resource("dynamodb", region_name="ap-northeast-1")
    return resource.create_table(
        TableName=TABLE_NAME,
        BillingMode="PAY_PER_REQUEST",
        AttributeDefinitions=[
            {"AttributeName": "templateId", "AttributeType": "S"},
        ],
        KeySchema=[
            {"AttributeName": "templateId", "KeyType": "HASH"},
        ],
    )


@pytest.mark.asyncio
async def test_lists_every_stored_template():
    """Every row in the table comes back."""
    with mock_aws():
        table = _create_table()
        table.put_item(Item=CAFE)
        table.put_item(Item=HOTEL)

        templates = await DynamoDbScenesTemplateRepository(
            table_name=TABLE_NAME,
        ).list_all()

    by_id = {t.template_id: t for t in templates}
    assert set(by_id) == {"tpl_cafe", "tpl_hotel"}
    assert by_id["tpl_cafe"].title == "Cafe"
    assert by_id["tpl_hotel"].thumbnail_uri == "assets/templates/tpl_hotel.jpg"


@pytest.mark.asyncio
async def test_keeps_the_order_and_the_duplicates():
    """Two dish clips is an ordinary template, not a mistake."""
    with mock_aws():
        table = _create_table()
        table.put_item(Item=CAFE)

        templates = await DynamoDbScenesTemplateRepository(
            table_name=TABLE_NAME,
        ).list_all()

    assert templates[0].scene_principals == [
        "shop_gaikan",
        "main_dish",
        "main_dish",
    ]


@pytest.mark.asyncio
async def test_returns_nothing_from_an_empty_table():
    """An empty table is not an error."""
    with mock_aws():
        _create_table()

        templates = await DynamoDbScenesTemplateRepository(
            table_name=TABLE_NAME,
        ).list_all()

    assert templates == []


@pytest.mark.asyncio
async def test_reads_beyond_a_single_scan_page():
    """A scan that stops early is continued, not silently truncated."""
    with mock_aws():
        table = _create_table()
        for index in range(30):
            table.put_item(
                Item={**CAFE, "templateId": f"tpl_{index:02d}"},
            )

        repository = DynamoDbScenesTemplateRepository(table_name=TABLE_NAME)
        templates = await repository.list_all()

    assert len(templates) == 30


@pytest.mark.asyncio
async def test_gets_one_template_by_id():
    """A single template is fetched by key, not by scanning."""
    with mock_aws():
        table = _create_table()
        table.put_item(Item=CAFE)
        table.put_item(Item=HOTEL)

        template = await DynamoDbScenesTemplateRepository(
            table_name=TABLE_NAME,
        ).get(template_id="tpl_hotel")

    assert template is not None
    assert template.title == "Hotel"
    assert template.thumbnail_uri == "assets/templates/tpl_hotel.jpg"


@pytest.mark.asyncio
async def test_answers_nothing_for_an_unknown_id():
    """An unknown identifier is not an error the caller has to catch."""
    with mock_aws():
        _create_table()

        template = await DynamoDbScenesTemplateRepository(
            table_name=TABLE_NAME,
        ).get(template_id="tpl_nowhere")

    assert template is None


def test_implements_the_core_abstraction():
    """The application layer only ever sees the abstraction."""
    assert issubclass(
        DynamoDbScenesTemplateRepository,
        BaseScenesTemplateRepository,
    )
