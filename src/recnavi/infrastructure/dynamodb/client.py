# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.


"""DynamoDB client."""

import boto3

from recnavi.config.variables import REGION


def get_table(table_name: str):
    """Get a handle on one DynamoDB table."""
    resource = boto3.resource("dynamodb", region_name=REGION)
    return resource.Table(table_name)


def scan_all(table_name: str) -> list[dict]:
    """Read every item of a table.

    A scan stops at one megabyte, so a table larger than that comes back
    in pages. Following LastEvaluatedKey is what stops the caller from
    silently seeing only the first page.
    """
    table = get_table(table_name)
    items: list[dict] = []
    arguments: dict = {}
    while True:
        response = table.scan(**arguments)
        items.extend(response["Items"])
        last_key = response.get("LastEvaluatedKey")
        if not last_key:
            return items
        arguments["ExclusiveStartKey"] = last_key


def get_item(table_name: str, key: dict) -> dict | None:
    """Read one item by its key, or nothing when there is none."""
    response = get_table(table_name).get_item(Key=key)
    return response.get("Item")
