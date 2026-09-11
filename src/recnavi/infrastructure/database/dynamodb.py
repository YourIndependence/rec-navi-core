# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.

"""DynamoDB implementation with Decimal conversion."""

from decimal import Decimal
from typing import Any

import aioboto3

from recnavi.core.database.base_database import BaseDatabase


def _convert_to_dynamodb_format(item: dict[str, Any]) -> dict[str, Any]:
    """Convert Python types to DynamoDB-compatible format.

    Converts int and float to Decimal to avoid type errors in DynamoDB.

    Args:
        item: Dictionary with Python native types.

    Returns:
        Dictionary with DynamoDB-compatible types.

    """
    converted = {}
    for key, value in item.items():
        if isinstance(value, float | int) and not isinstance(value, bool):
            converted[key] = Decimal(str(value))
        elif isinstance(value, dict):
            converted[key] = _convert_to_dynamodb_format(value)
        elif isinstance(value, list):
            converted[key] = [
                (
                    _convert_to_dynamodb_format(v)
                    if isinstance(v, dict)
                    else Decimal(str(v))
                    if isinstance(v, float | int) and not isinstance(v, bool)
                    else v
                )
                for v in value
            ]
        else:
            converted[key] = value
    return converted


def _convert_from_dynamodb_format(item: dict[str, Any]) -> dict[str, Any]:
    """Convert DynamoDB types to Python native types.

    Converts Decimal back to int or float for application use.

    Args:
        item: Dictionary with DynamoDB types.

    Returns:
        Dictionary with Python native types.

    """
    converted = {}
    for key, value in item.items():
        if isinstance(value, Decimal):
            # Convert Decimal to int if it has no fractional part
            converted[key] = int(value) if value % 1 == 0 else float(value)
        elif isinstance(value, dict):
            converted[key] = _convert_from_dynamodb_format(value)
        elif isinstance(value, list):
            converted[key] = [
                _convert_from_dynamodb_format(v)
                if isinstance(v, dict)
                else (
                    int(v)
                    if isinstance(v, Decimal) and v % 1 == 0
                    else float(v)
                    if isinstance(v, Decimal)
                    else v
                )
                for v in value
            ]
        else:
            converted[key] = value
    return converted


class DynamoDb(BaseDatabase):
    """DynamoDB implementation with automatic Decimal conversion.

    Handles conversion between Python native types (int, float) and
    DynamoDB Decimal type transparently.
    """

    def __init__(self, table_name: str):
        """Initialize DynamoDb with table name.

        Args:
            table_name: Name of the DynamoDB table.

        """
        self.table_name = table_name
        self.session = aioboto3.Session()

    async def get_item(self, key: dict[str, Any]) -> dict[str, Any] | None:
        """Get an item by primary key.

        Args:
            key: Primary key as a dictionary.

        Returns:
            Item as a dictionary with Python native types if found, None otherwise.

        """
        async with self.session.resource("dynamodb") as dynamodb:
            table = await dynamodb.Table(self.table_name)
            response = await table.get_item(Key=key)
            item = response.get("Item")
            return _convert_from_dynamodb_format(item) if item else None

    async def put_item(self, item: dict[str, Any]) -> None:
        """Put an item into the table.

        Args:
            item: Item to store with Python native types.

        """
        converted_item = _convert_to_dynamodb_format(item)
        async with self.session.resource("dynamodb") as dynamodb:
            table = await dynamodb.Table(self.table_name)
            await table.put_item(Item=converted_item)

    async def query(
        self,
        key_condition: dict[str, Any],
        _filter_expression: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """Query items by key condition.

        Args:
            key_condition: Key condition for the query.
            _filter_expression: Optional filter expression (reserved for future use).

        Returns:
            List of items with Python native types matching the query.

        """
        async with self.session.resource("dynamodb") as dynamodb:
            table = await dynamodb.Table(self.table_name)
            response = await table.query(**key_condition)
            items = response.get("Items", [])
            return [_convert_from_dynamodb_format(item) for item in items]

    async def delete_item(self, key: dict[str, Any]) -> None:
        """Delete an item by primary key.

        Args:
            key: Primary key as a dictionary.

        """
        async with self.session.resource("dynamodb") as dynamodb:
            table = await dynamodb.Table(self.table_name)
            await table.delete_item(Key=key)
