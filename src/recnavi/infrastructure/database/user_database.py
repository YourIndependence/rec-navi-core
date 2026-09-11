# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.

"""DynamoDB implementation for users table."""

import asyncio
from typing import Any

import boto3

from recnavi.core.database.base_database import BaseDatabase


class UserDatabase(BaseDatabase):
    """DynamoDB implementation for users table operations."""

    def __init__(self, table_name: str):
        """Initialize UserDatabase with table name.

        Args:
            table_name: Name of the DynamoDB users table.

        """
        self.table_name = table_name
        self.dynamodb = boto3.resource("dynamodb")
        self.table = self.dynamodb.Table(table_name)

    async def get_item(self, key: dict[str, Any]) -> dict[str, Any] | None:
        """Get a user by primary key.

        Args:
            key: Primary key as a dictionary. Example: {"userId": "abc123"}

        Returns:
            User item as a dictionary if found, None otherwise.

        """
        response = await asyncio.to_thread(self.table.get_item, Key=key)
        return response.get("Item")

    async def put_item(self, item: dict[str, Any]) -> None:
        """Put a user item into the table.

        Args:
            item: User item to store. Must include userId as primary key.

        """
        await asyncio.to_thread(self.table.put_item, Item=item)

    async def query(
        self,
        key_condition: dict[str, Any],
        _filter_expression: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """Query users by key condition.

        Args:
            key_condition: Key condition for the query.
            _filter_expression: Optional filter expression (reserved for future use).

        Returns:
            List of user items matching the query.

        """
        response = await asyncio.to_thread(self.table.query, **key_condition)
        return response.get("Items", [])

    async def delete_item(self, key: dict[str, Any]) -> None:
        """Delete a user by primary key.

        Args:
            key: Primary key as a dictionary. Example: {"userId": "abc123"}

        """
        await asyncio.to_thread(self.table.delete_item, Key=key)
