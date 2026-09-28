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
from boto3.dynamodb.conditions import Key

from recnavi.config.variables import REGION
from recnavi.core.database.base_database import BaseDatabase
from recnavi.core.database.base_database import DatabaseQueryResult


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
    ) -> DatabaseQueryResult:
        """Query items by key condition with optional pagination.

        Args:
            key_condition: Key condition for the query.
            filter_expression: Optional attribute equality filters.
            Multiple filters are combined with AND.
            index: Optional global or local secondary index name.
            limit: Maximum number of items to return.
            exclusive_start_key: Primary key of item to start from (for pagination).

        Returns:
            DatabaseQueryResult with items and optional last_evaluated_key.

        """
        async with self.session.resource("dynamodb") as dynamodb:
            table = await dynamodb.Table(self.table_name)
            query_kwargs = _build_query_kwargs(key_condition)
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
            return DatabaseQueryResult(
                items=[_convert_from_dynamodb_format(item) for item in items],
                last_evaluated_key=last_evaluated_key,
            )

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
        limit: int | None = None,
        exclusive_start_key: dict[str, Any] | None = None,
    ) -> DatabaseQueryResult:
        """Scan all items in the table with optional pagination.

        Warning: Full table scan. Only use for small tables.

        Args:
            filter_expression: Optional attribute equality filters.
            Multiple filters are combined with AND.
            limit: Maximum number of items to return.
            exclusive_start_key: Primary key of item to start from (for pagination).

        Returns:
            DatabaseQueryResult with items and optional last_evaluated_key.

        """
        async with self.session.resource("dynamodb") as dynamodb:
            table = await dynamodb.Table(self.table_name)
            scan_kwargs: dict[str, object] = {}
            condition = _build_filter_expression(filter_expression)
            if condition is not None:
                scan_kwargs["FilterExpression"] = condition
            if limit is not None:
                scan_kwargs["Limit"] = limit
            if exclusive_start_key is not None:
                scan_kwargs["ExclusiveStartKey"] = exclusive_start_key
            response = await table.scan(**scan_kwargs)
            items = response.get("Items", [])
            last_evaluated_key = response.get("LastEvaluatedKey")
            return DatabaseQueryResult(
                items=[_convert_from_dynamodb_format(item) for item in items],
                last_evaluated_key=last_evaluated_key,
            )


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


def _build_query_kwargs(key_condition: dict[str, Any]) -> dict[str, Any]:
    """Build DynamoDB query arguments from the database abstraction input."""
    conditions = [
        Key(attribute).eq(value) for attribute, value in key_condition.items()
    ]
    expression = conditions[0]
    for condition in conditions[1:]:
        expression &= condition
    return {"KeyConditionExpression": expression}


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
