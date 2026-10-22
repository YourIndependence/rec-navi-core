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

from recnavi.core.types.database import DatabaseQueryResult


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
    async def put_item(
        self,
        item: dict[str, Any],
        condition_expression: str | None = None,
        expression_attribute_values: dict[str, Any] | None = None,
    ) -> None:
        """Put an item into the table.

        Args:
            item: Item to store as a dictionary. Must include primary key.
            condition_expression: Optional condition that must hold for the
                write to succeed (e.g., "version = :expected_version").
            expression_attribute_values: Values referenced by the condition.

        Raises:
            ClientConflictError: The condition expression was not satisfied.

        """
        pass

    @abstractmethod
    async def update_item(
        self,
        *,
        key: dict[str, Any],
        update_expression: str,
        condition_expression: str | None = None,
        expression_attribute_names: dict[str, str] | None = None,
        expression_attribute_values: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Update an item with an update expression.

        Args:
            key: Primary key (and sort key if applicable) as a dictionary.
            update_expression: Update expression (e.g., "SET #n = :n").
            condition_expression: Optional condition that must hold for the
                update to succeed.
            expression_attribute_names: Placeholders for attribute names.
            expression_attribute_values: Values referenced by the expressions.

        Returns:
            The updated item.

        Raises:
            ClientConflictError: The condition expression was not satisfied.

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
        limit: int | None = None,
        exclusive_start_key: dict[str, Any] | None = None,
    ) -> DatabaseQueryResult:
        """Scan all items in the table with optional pagination.

        Args:
            filter_expression: Optional filter expression to apply.
            limit: Maximum number of items to return.
            exclusive_start_key: Primary key of item to start from (for pagination).

        Returns:
            DatabaseQueryResult with items and optional last_evaluated_key.

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
    ) -> DatabaseQueryResult:
        """Query items by key condition with optional pagination.

        Args:
            key_condition: Key condition for the query.
            filter_expression: Optional filter expression.
            index: Optional global or local secondary index name.
            limit: Maximum number of items to return.
            exclusive_start_key: Primary key of item to start from (for pagination).

        Returns:
            DatabaseQueryResult with items and optional last_evaluated_key.

        """
        pass
