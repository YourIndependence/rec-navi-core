# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.

"""DynamoDB implementation with Decimal conversion."""

import json
from decimal import Decimal
from typing import Any

import aioboto3
from boto3.dynamodb.conditions import Attr
from boto3.dynamodb.conditions import ConditionBase

from recnavi.config.variables import REGION
from recnavi.core.database.base_database import BaseDatabase


class DynamoDb(BaseDatabase):
    """DynamoDB"""

    def __init__(self, table_name: str):
        """Initialize DynamoDb with table name.

        Args:
            table_name: Name of the DynamoDB table.

        """
        self.table_name = table_name
        self.session = aioboto3.Session(region_name=REGION)

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

    async def put_item(
        self,
        item: dict[str, Any],
        condition_expression: str | None = None,
        expression_attribute_values: dict[str, Any] | None = None,
    ) -> None:
        """Put an item into the table with optional condition.

        Args:
            item: Item to store with Python native types.
            condition_expression: Optional DynamoDB condition expression.
            expression_attribute_values: Values for condition expression placeholders.

        Raises:
            ClientConflictError: Condition check failed (409).

        """
        from botocore.exceptions import ClientError

        from recnavi.exceptions.exceptions import ClientConflictError

        converted_item = _convert_to_dynamodb_format(item)
        async with self.session.resource("dynamodb") as dynamodb:
            table = await dynamodb.Table(self.table_name)
            put_kwargs: dict[str, Any] = {"Item": converted_item}
            if condition_expression is not None:
                put_kwargs["ConditionExpression"] = condition_expression
            if expression_attribute_values is not None:
                put_kwargs["ExpressionAttributeValues"] = (
                    expression_attribute_values
                )

            try:
                await table.put_item(**put_kwargs)
            except ClientError as error:
                if (
                    error.response["Error"]["Code"]
                    == "ConditionalCheckFailedException"
                ):
                    raise ClientConflictError(
                        f"ConditionalCheckFailedException: {error.response['Error']['Message']}",
                    ) from error
                raise

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
            filter_expression: Optional attribute equality filters.
            Multiple filters are combined with AND.
            index: Optional global or local secondary index name.
            limit: Maximum number of items to return.
            exclusive_start_key: Primary key of item to start from (for pagination).

        Returns:
            Tuple of (items, last_evaluated_key). last_evaluated_key is None
            if there are no more items to retrieve.

        """
        async with self.session.resource("dynamodb") as dynamodb:
            table = await dynamodb.Table(self.table_name)
            query_kwargs = dict(key_condition)
            condition = _build_filter_expression(filter_expression)
            if condition is not None:
                query_kwargs["FilterExpression"] = condition
            if index is not None:
                query_kwargs["IndexName"] = index
            if limit is not None:
                query_kwargs["Limit"] = limit
            if exclusive_start_key is not None:
                query_kwargs["ExclusiveStartKey"] = exclusive_start_key
            response = await table.query(**query_kwargs)
            items = response.get("Items", [])
            last_evaluated_key = response.get("LastEvaluatedKey")
            return (
                [_convert_from_dynamodb_format(item) for item in items],
                last_evaluated_key,
            )

    async def update_item(
        self,
        *,
        key: dict[str, Any],
        update_expression: str,
        condition_expression: str | None = None,
        expression_attribute_names: dict[str, str] | None = None,
        expression_attribute_values: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Update item with UpdateExpression.

        Args:
            key: Primary key of item to update.
            update_expression: DynamoDB UpdateExpression (e.g., "SET status = :status").
            condition_expression: Optional condition (e.g., "sceneId = :sceneId").
            expression_attribute_names: Attribute name substitutions.
            expression_attribute_values: Value substitutions.

        Returns:
            Updated item with Python native types.

        Raises:
            ClientConflictError: Condition check failed.

        """
        from botocore.exceptions import ClientError

        from recnavi.exceptions.exceptions import ClientConflictError

        converted_values = (
            _convert_to_dynamodb_format(expression_attribute_values)
            if expression_attribute_values
            else None
        )

        async with self.session.resource("dynamodb") as dynamodb:
            table = await dynamodb.Table(self.table_name)
            update_kwargs: dict[str, Any] = {
                "Key": key,
                "UpdateExpression": update_expression,
                "ReturnValues": "ALL_NEW",
            }

            if condition_expression is not None:
                update_kwargs["ConditionExpression"] = condition_expression

            if expression_attribute_names is not None:
                update_kwargs["ExpressionAttributeNames"] = (
                    expression_attribute_names
                )

            if converted_values is not None:
                update_kwargs["ExpressionAttributeValues"] = converted_values

            try:
                response = await table.update_item(**update_kwargs)
                item = response["Attributes"]
                return _convert_from_dynamodb_format(item)
            except ClientError as error:
                if (
                    error.response["Error"]["Code"]
                    == "ConditionalCheckFailedException"
                ):
                    raise ClientConflictError(
                        f"ConditionalCheckFailedException: {error.response['Error']['Message']}",
                    ) from error
                raise

    async def delete_item(self, key: dict[str, Any]) -> None:
        """Delete an item by primary key.

        Args:
            key: Primary key as a dictionary.

        """
        async with self.session.resource("dynamodb") as dynamodb:
            table = await dynamodb.Table(self.table_name)
            await table.delete_item(Key=key)

    async def scan(
        self,
        filter_expression: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """Scan all items in the table.

        Warning: Full table scan. Only use for small tables.

        Args:
            filter_expression: Optional attribute equality filters.
            Multiple filters are combined with AND.

        Returns:
            List of all items with Python native types.

        """
        async with self.session.resource("dynamodb") as dynamodb:
            table = await dynamodb.Table(self.table_name)
            scan_kwargs: dict[str, object] = {}
            condition = _build_filter_expression(filter_expression)
            if condition is not None:
                scan_kwargs["FilterExpression"] = condition
            response = await table.scan(**scan_kwargs)
            items = response.get("Items", [])
            return [_convert_from_dynamodb_format(item) for item in items]


def _build_filter_expression(
    filter_expression: dict[str, Any] | None,
) -> ConditionBase | None:
    """Build a DynamoDB AND expression from attribute equality filters."""
    if not filter_expression:
        return None

    conditions = [
        Attr(attribute).eq(value)
        for attribute, value in filter_expression.items()
    ]
    expression = conditions[0]
    for condition in conditions[1:]:
        expression &= condition
    return expression


def _decimal_to_num(obj: Any) -> int | float | object | None:
    """Convert Decimal values to Python numbers."""
    if isinstance(obj, Decimal):
        return int(obj) if float(obj).is_integer() else float(obj)
    return None


def _convert_to_dynamodb_format(item: dict[str, Any]) -> dict[str, Any]:
    """Convert Python numbers to DynamoDB Decimal values."""
    return json.loads(
        json.dumps(item, default=_decimal_to_num),
        parse_float=Decimal,
        parse_int=Decimal,
    )


def _convert_from_dynamodb_format(item: dict[str, Any]) -> dict[str, Any]:
    """Convert DynamoDB Decimal values to Python numbers."""
    return json.loads(
        json.dumps(
            item,
            default=_decimal_to_num,
        ),
    )
