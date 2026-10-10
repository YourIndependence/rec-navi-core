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
from recnavi.exceptions.exceptions import ClientResourcesNotFoundError


class MockDatabase(BaseDatabase):
    """In-memory mock database for unit testing."""

    def __init__(self, initial_items: list[dict[str, Any]] | None = None):
        """Initialize mock database with optional initial items."""
        self.items: list[dict[str, Any]] = initial_items or []

    async def get_item(self, key: dict[str, Any]) -> dict[str, Any] | None:
        """Get an item by primary key."""
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
        """Put an item into the database with optional condition."""

        if (
            condition_expression is not None
            and expression_attribute_values is not None
        ):
            for i, existing_item in enumerate(self.items):
                if self._is_same_key(item, existing_item):
                    if not self._check_condition(
                        existing_item,
                        condition_expression,
                        expression_attribute_values,
                    ):
                        raise ClientConflictError("Condition check failed")
                    self.items[i] = item
                    return
            raise ClientConflictError("Item not found for conditional update")

        for i, existing_item in enumerate(self.items):
            if self._is_same_key(item, existing_item):
                self.items[i] = item
                return

        self.items.append(item)

    def _is_same_key(
        self,
        item1: dict[str, Any],
        item2: dict[str, Any],
    ) -> bool:
        """Check if two items have the same primary key."""
        key_fields = ["projectId", "userId", "sceneId", "templateId"]
        for key_field in key_fields:
            if key_field in item1 and key_field in item2:
                return item1[key_field] == item2[key_field]
        return False

    def _check_condition(
        self,
        item: dict[str, Any],
        condition_expression: str,
        expression_attribute_values: dict[str, Any],
    ) -> bool:
        """Check if condition expression is satisfied."""
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
        """Query items by key condition with optional pagination."""
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
        """Update item with UpdateExpression (simplified for testing)."""

        item = await self.get_item(key)
        if not item:
            raise ClientResourcesNotFoundError("Item not found")

        if (
            condition_expression
            and expression_attribute_values
            and not self._check_update_condition(
                item,
                condition_expression,
                expression_attribute_values,
            )
        ):
            raise ClientConflictError("Condition check failed")

        self._apply_update_expression(
            item,
            update_expression,
            expression_attribute_names or {},
            expression_attribute_values or {},
        )

        await self.put_item(item)
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
        if match:
            index = int(match.group(1))
            expected_scene_id = expression_attribute_values.get(":sceneId")
            if index < len(item.get("scenes", [])):
                actual_scene_id = item["scenes"][index].get("sceneId")
                return actual_scene_id == expected_scene_id
            return False

        return True

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
            field_name = match.group(2)
            value_key = f":{match.group(3)}"

            if field_name.startswith("#"):
                field_name = expression_attribute_names.get(
                    field_name,
                    field_name[1:],
                )

            camel_field = self._to_camel_case(field_name)
            if index < len(item.get("scenes", [])):
                item["scenes"][index][camel_field] = (
                    expression_attribute_values[value_key]
                )

        top_level_pattern = r"(?<!scenes\[\d\]\.)(\#?\w+) = :(\w+)"
        for match in re.finditer(top_level_pattern, update_expression):
            field_name = match.group(1)
            value_key = f":{match.group(2)}"

            if field_name.startswith("#"):
                field_name = expression_attribute_names.get(
                    field_name,
                    field_name[1:],
                )

            camel_field = self._to_camel_case(field_name)
            if value_key in expression_attribute_values:
                item[camel_field] = expression_attribute_values[value_key]

    def _to_camel_case(self, field: str) -> str:
        """Convert field name to camelCase (preserves if already camelCase)."""
        if "_" in field:
            parts = field.split("_")
            return parts[0] + "".join(word.capitalize() for word in parts[1:])
        return field

    async def delete_item(self, key: dict[str, Any]) -> None:
        """Delete an item by primary key."""
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
        """Scan all items in the database with optional pagination."""
        if not filter_expression:
            results = self.items.copy()
        else:
            results = [
                item
                for item in self.items
                if all(item.get(k) == v for k, v in filter_expression.items())
            ]

        return self._paginate_results(results, limit, exclusive_start_key)
