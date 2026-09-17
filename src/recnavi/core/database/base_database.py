# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.

"""Base database interface for all table operations."""

from abc import ABC
from abc import abstractmethod
from typing import Any


class BaseDatabase(ABC):
    """Abstract base class for database table operations.

    This interface defines common operations for interacting with database
    tables. Concrete implementations handle specific database technologies
    (e.g., DynamoDB, PostgreSQL).
    """

    @abstractmethod
    async def get_item(self, key: dict[str, Any]) -> dict[str, Any] | None:
        """Get a single item by primary key.

        Args:
            key: Primary key (and sort key if applicable) as a dictionary.
                 Example: {"userId": "abc123"}

        Returns:
            Item as a dictionary if found, None otherwise.

        """
        pass

    @abstractmethod
    async def put_item(self, item: dict[str, Any]) -> None:
        """Put an item into the table.

        Args:
            item: Item to store as a dictionary. Must include primary key.

        """
        pass

    @abstractmethod
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
            index: Optional global or local secondary index name.
            limit: Maximum number of items to return.
            exclusive_start_key: Primary key of item to start from (for pagination).

        Returns:
            Tuple of (items, last_evaluated_key). last_evaluated_key is None
            if there are no more items to retrieve.

        """
        pass

    @abstractmethod
    async def delete_item(self, key: dict[str, Any]) -> None:
        """Delete an item by primary key.

        Args:
            key: Primary key (and sort key if applicable) as a dictionary.

        """
        pass

    @abstractmethod
    async def scan(
        self,
        filter_expression: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """Scan all items in the table.

        Warning: This is a full table scan and should only be used for small
        tables or with appropriate filters.

        Args:
            filter_expression: Optional filter expression to apply.

        Returns:
            List of all items in the table (or matching the filter).

        """
        pass
