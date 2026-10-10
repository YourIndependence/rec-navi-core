# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.

"""Mock database for unit testing."""

import re
from typing import Any

from recnavi.core.database.base_database import BaseDatabase
from recnavi.core.database.base_database import DatabaseQueryResult
from recnavi.exceptions.exceptions import ClientConflictError
from recnavi.exceptions.exceptions import ClientNotFoundError


_DEFAULT_KEY_FIELDS = ("projectId", "userId", "sceneId", "templateId")


class MockDatabase(BaseDatabase):
    """In-memory mock database for unit testing."""

    def __init__(
        self,
        initial_items: list[dict[str, Any]] | None = None,
        key_names: tuple[str, ...] | None = None,
    ):
        """Initialize mock database with optional initial items.

        Args:
            initial_items: List of items to pre-populate the database.
            key_names: Primary key attribute names. When given, put_item
                replaces an existing item with the same key like a real table.

        """
        self.items: list[dict[str, Any]] = initial_items or []
        self.key_names = key_names

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

    async def put_item(
        self,
        item: dict[str, Any],
        condition_expression: str | None = None,
        expression_attribute_values: dict[str, Any] | None = None,
    ) -> None:
        """Put an item into the database with an optional condition.

        An existing item with the same primary key is replaced. The key is
        key_names when given, otherwise the first of the well-known key
        attributes present on both items.

        Args:
            item: Item to store.
            condition_expression: Optional condition on the existing item
                (only "version = :expected_version" is evaluated).
            expression_attribute_values: Values referenced by the condition.

        Raises:
            ClientConflictError: The condition failed or no item exists.

        """
        existing_index = self._find_same_key_index(item)
        if condition_expression is not None:
            if existing_index is None:
                raise ClientConflictError("Item not found for conditional put")
            if not self._check_condition(
                self.items[existing_index],
                condition_expression,
                expression_attribute_values or {},
            ):
                raise ClientConflictError("Condition check failed")

        if existing_index is None:
            self.items.append(item)
        else:
            self.items[existing_index] = item

    def _find_same_key_index(self, item: dict[str, Any]) -> int | None:
        """Return the index of the stored item sharing the item's key."""
        for index, existing_item in enumerate(self.items):
            if self._is_same_key(item, existing_item):
                return index
        return None

    def _is_same_key(
        self,
        item1: dict[str, Any],
        item2: dict[str, Any],
    ) -> bool:
        """Check if two items have the same primary key."""
        if self.key_names:
            return all(item1.get(k) == item2.get(k) for k in self.key_names)
        for key_field in _DEFAULT_KEY_FIELDS:
            if key_field in item1 and key_field in item2:
                return item1[key_field] == item2[key_field]
        return False

    def _check_condition(
        self,
        item: dict[str, Any],
        condition_expression: str,
        expression_attribute_values: dict[str, Any],
    ) -> bool:
        """Check if a put condition expression is satisfied."""
        if "version = :expected_version" in condition_expression:
            expected_version = expression_attribute_values.get(
                ":expected_version",
            )
            return item.get("version") == expected_version
        return True

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
            index: Optional index name (ignored in mock).
            limit: Maximum number of items to return.
            exclusive_start_key: Primary key to start from (for pagination).

        Returns:
            DatabaseQueryResult with items and optional last_evaluated_key.

        """
        results = self._filter_items(key_condition, filter_expression)
        return self._paginate_results(results, limit, exclusive_start_key)

    def _filter_items(
        self,
        key_condition: dict[str, Any],
        filter_expression: dict[str, Any] | None,
    ) -> list[dict[str, Any]]:
        """Filter items by key condition and optional filter expression."""
        results = []
        for item in self.items:
            if all(item.get(k) == v for k, v in key_condition.items()) and (
                not filter_expression
                or all(item.get(k) == v for k, v in filter_expression.items())
            ):
                results.append(item)
        return results

    def _paginate_results(
        self,
        results: list[dict[str, Any]],
        limit: int | None,
        exclusive_start_key: dict[str, Any] | None,
    ) -> DatabaseQueryResult:
        """Paginate query results with limit and exclusive start key."""
        start_index = self._find_start_index(results, exclusive_start_key)

        if limit is not None:
            end_index = start_index + limit
            paginated_results = results[start_index:end_index]
            last_evaluated_key = (
                paginated_results[-1] if end_index < len(results) else None
            )
        else:
            paginated_results = results[start_index:]
            last_evaluated_key = None

        return DatabaseQueryResult(
            items=paginated_results,
            last_evaluated_key=last_evaluated_key,
        )

    def _find_start_index(
        self,
        results: list[dict[str, Any]],
        exclusive_start_key: dict[str, Any] | None,
    ) -> int:
        """Find starting index for pagination from exclusive start key."""
        if exclusive_start_key is None:
            return 0

        for i, item in enumerate(results):
            if all(item.get(k) == v for k, v in exclusive_start_key.items()):
                return i + 1
        return 0

    async def update_item(
        self,
        *,
        key: dict[str, Any],
        update_expression: str,
        condition_expression: str | None = None,
        expression_attribute_names: dict[str, str] | None = None,
        expression_attribute_values: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Apply SET assignments to an item (simplified parser).

        Supports top-level "field = :value" and "scenes[i].field = :value"
        assignments, "#name" placeholders, and the condition
        "scenes[i].sceneId = :sceneId".

        Raises:
            ClientNotFoundError: No item matches the key.
            ClientConflictError: The condition expression is not satisfied.

        """
        item = await self.get_item(key)
        if not item:
            raise ClientNotFoundError("Item not found")

        names = expression_attribute_names or {}
        values = expression_attribute_values or {}
        if condition_expression and not self._check_update_condition(
            item,
            condition_expression,
            values,
        ):
            raise ClientConflictError("Condition check failed")

        self._apply_update_expression(item, update_expression, names, values)
        return item

    def _check_update_condition(
        self,
        item: dict[str, Any],
        condition_expression: str,
        expression_attribute_values: dict[str, Any],
    ) -> bool:
        """Check if update condition expression is satisfied."""
        match = re.search(
            r"scenes\[(\d+)\]\.sceneId = :sceneId",
            condition_expression,
        )
        if match is None:
            return True
        index = int(match.group(1))
        scenes = item.get("scenes", [])
        if index >= len(scenes):
            return False
        expected_scene_id = expression_attribute_values.get(":sceneId")
        return scenes[index].get("sceneId") == expected_scene_id

    def _apply_update_expression(
        self,
        item: dict[str, Any],
        update_expression: str,
        expression_attribute_names: dict[str, str],
        expression_attribute_values: dict[str, Any],
    ) -> None:
        """Apply SET operations from UpdateExpression (simplified parser)."""
        scene_pattern = r"scenes\[(\d+)\]\.(\#?\w+) = :(\w+)"
        for match in re.finditer(scene_pattern, update_expression):
            index = int(match.group(1))
            field_name = self._resolve_name(
                match.group(2),
                expression_attribute_names,
            )
            value_key = f":{match.group(3)}"
            if index < len(item.get("scenes", [])):
                item["scenes"][index][field_name] = (
                    expression_attribute_values[value_key]
                )

        top_level_pattern = r"(?<!scenes\[\d\]\.)(\#?\w+) = :(\w+)"
        for match in re.finditer(top_level_pattern, update_expression):
            field_name = self._resolve_name(
                match.group(1),
                expression_attribute_names,
            )
            value_key = f":{match.group(2)}"
            if value_key in expression_attribute_values:
                item[field_name] = expression_attribute_values[value_key]

    def _resolve_name(
        self,
        field: str,
        expression_attribute_names: dict[str, str],
    ) -> str:
        """Resolve a #placeholder and convert snake_case to camelCase."""
        if field.startswith("#"):
            field = expression_attribute_names.get(field, field[1:])
        if "_" in field:
            parts = field.split("_")
            return parts[0] + "".join(word.capitalize() for word in parts[1:])
        return field

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
        limit: int | None = None,
        exclusive_start_key: dict[str, Any] | None = None,
    ) -> DatabaseQueryResult:
        """Scan all items in the database with optional pagination.

        Args:
            filter_expression: Optional filter expression.
            limit: Maximum number of items to return.
            exclusive_start_key: Primary key to start from (for pagination).

        Returns:
            DatabaseQueryResult with items and optional last_evaluated_key.

        """
        if not filter_expression:
            results = self.items.copy()
        else:
            results = [
                item
                for item in self.items
                if all(item.get(k) == v for k, v in filter_expression.items())
            ]

        return self._paginate_results(results, limit, exclusive_start_key)
