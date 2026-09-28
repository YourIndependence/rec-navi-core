# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.

"""Project listing domain logic."""

import base64
import json

from recnavi.core.database.base_database import BaseDatabase
from recnavi.core.types.project import Project


async def get_projects(
    projects_db: BaseDatabase,
    group_id: str,
    limit: int = 20,
    cursor: str | None = None,
) -> tuple[list[Project], str | None]:
    """Get projects for a group with pagination.

    Queries the projects table GSI1 (groupId + createdAt) in descending order
    to return newest projects first.

    Args:
        projects_db: Database instance for projects table.
        group_id: Group identifier (from authenticated user token).
        limit: Maximum items per page (1-100, default 20).
        cursor: Opaque pagination cursor from previous response.

    Returns:
        Tuple of (projects, next_cursor). next_cursor is None if last page.

    """

    def _encode_cursor(last_evaluated_key: dict | None) -> str | None:
        """Encode DynamoDB LastEvaluatedKey to opaque base64 cursor."""
        if not last_evaluated_key:
            return None
        json_str = json.dumps(last_evaluated_key, sort_keys=True)
        return base64.b64encode(json_str.encode()).decode()

    def _decode_cursor(cursor: str | None) -> dict | None:
        """Decode opaque base64 cursor to DynamoDB ExclusiveStartKey."""
        if not cursor:
            return None
        json_str = base64.b64decode(cursor.encode()).decode()
        return json.loads(json_str)

    exclusive_start_key = _decode_cursor(cursor)

    result = await projects_db.query(
        key_condition={"groupId": group_id},
        index="GSI1",
        limit=limit,
        exclusive_start_key=exclusive_start_key,
    )

    projects = [Project.model_validate(item) for item in result.items]
    next_cursor = _encode_cursor(result.last_evaluated_key)

    return projects, next_cursor
