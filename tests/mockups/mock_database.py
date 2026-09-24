# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.

"""Mock database for unit testing."""

from typing import Any

from recnavi.core.database.base_database import BaseDatabase


class MockDatabase(BaseDatabase):
    """In-memory mock database for unit testing."""

    def __init__(self, initial_items: list[dict[str, Any]] | None = None):
        """Initialize mock database with optional initial items.

        Args:
            initial_items: List of items to pre-populate the database.

        """
        self.items: list[dict[str, Any]] = initial_items or []

    async def get_item(self, key: dict[str, Any]) -> dict[str, Any] | None:
        """Get an item by primary key.

        Args:
            key: Primary key as a dictionary.

        Returns:
            Item if found, None otherwise.

        """
        for item in self.items:
            if all(item.get(k) == v for k, v in key.items()):
                return item
        return None

    async def put_item(self, item: dict[str, Any]) -> None:
        """Put an item into the database (upsert behavior).

        If an item with the same primary key exists, it will be replaced.
        Otherwise, the new item will be added.

        Args:
            item: Item to store.

        """
        primary_keys = self._get_primary_keys(item)
        if primary_keys:
            for i, existing_item in enumerate(self.items):
                if all(
                    existing_item.get(k) == v for k, v in primary_keys.items()
                ):
                    self.items[i] = item
                    return
        self.items.append(item)

    def _get_primary_keys(self, item: dict[str, Any]) -> dict[str, Any]:
        """Extract primary keys from an item.

        Common primary key patterns in this project:
        - scenePrincipal (scene masters)
        - templateId (templates)
        - projectId (projects)
        - userId (users)

        Args:
            item: Item to extract keys from.

        Returns:
            Dictionary of primary key fields.

        """
        key_fields = ["scenePrincipal", "templateId", "projectId", "userId"]
        return {k: v for k, v in item.items() if k in key_fields}

    async def query(
        self,
        key_condition: dict[str, Any],
        filter_expression: dict[str, Any] | None = None,
        index: str | None = None,
    ) -> list[dict[str, Any]]:
        """Query items by key condition.

        Args:
            key_condition: Key condition for the query.
            filter_expression: Optional filter expression.
            index: Optional index.

        Returns:
            List of items matching the query.

        """
        results = []
        for item in self.items:
            if all(item.get(k) == v for k, v in key_condition.items()) and (
                not filter_expression
                or all(item.get(k) == v for k, v in filter_expression.items())
            ):
                results.append(item)
        return results

    async def delete_item(self, key: dict[str, Any]) -> None:
        """Delete an item by primary key.

        Args:
            key: Primary key as a dictionary.

        """
        self.items = [
            item
            for item in self.items
            if not all(item.get(k) == v for k, v in key.items())
        ]

    async def scan(
        self,
        filter_expression: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """Scan all items in the database.

        Args:
            filter_expression: Optional filter expression.

        Returns:
            List of all items (or matching the filter).

        """
        if not filter_expression:
            return self.items.copy()

        return [
            item
            for item in self.items
            if all(item.get(k) == v for k, v in filter_expression.items())
        ]
