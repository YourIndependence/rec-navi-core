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
        """Put an item into the database.

        Args:
            item: Item to store.

        """
        self.items.append(item)

    async def query(
        self,
        key_condition: dict[str, Any],
        filter_expression: dict[str, Any] | None = None,
        index: str | None = None,
        limit: int | None = None,
        exclusive_start_key: dict[str, Any] | None = None,
    ) -> tuple[list[dict[str, Any]], dict[str, Any] | None]:
        """Query items by key condition with optional pagination.

        Args:
            key_condition: Key condition for the query.
            filter_expression: Optional filter expression.
            index: Optional index name (ignored in mock).
            limit: Maximum number of items to return.
            exclusive_start_key: Primary key to start from (for pagination).

        Returns:
            Tuple of (items, last_evaluated_key). last_evaluated_key is None
            if there are no more items.

        """
        # Simple mock implementation: filter by key_condition
        # In real DynamoDB, this would parse KeyConditionExpression
        results = []
        for item in self.items:
            if all(item.get(k) == v for k, v in key_condition.items()) and (
                not filter_expression
                or all(item.get(k) == v for k, v in filter_expression.items())
            ):
                results.append(item)

        # Handle pagination
        start_index = 0
        if exclusive_start_key is not None:
            # Find the starting position
            for i, item in enumerate(results):
                if all(
                    item.get(k) == v for k, v in exclusive_start_key.items()
                ):
                    start_index = i + 1
                    break

        # Apply limit
        if limit is not None:
            end_index = start_index + limit
            paginated_results = results[start_index:end_index]

            # Determine if there are more items
            if end_index < len(results):
                last_evaluated_key = paginated_results[-1]
            else:
                last_evaluated_key = None
        else:
            paginated_results = results[start_index:]
            last_evaluated_key = None

        return (paginated_results, last_evaluated_key)

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
