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
import logging
from collections.abc import Awaitable
from collections.abc import Callable

from recnavi.core.database.base_database import BaseDatabase
from recnavi.core.types.project import Project
from recnavi.core.types.project_filter_stats import ProjectFilterStats


logger = logging.getLogger(__name__)

FILTER_RATIO_WARNING_THRESHOLD = 80.0


async def get_projects(
    *,
    projects_db: BaseDatabase,
    user_id: str,
    group_id: str,
    limit: int = 20,
    cursor: str | None = None,
    record_metrics: Callable[[ProjectFilterStats], Awaitable[None]]
    | None = None,
) -> tuple[list[Project], str | None]:
    """Get projects assigned to user_id with pagination.

    Args:
        projects_db: Database instance.
        user_id: User identifier.
        group_id: User group identifier.
        limit: Maximum items per page.
        cursor: Opaque pagination cursor from the previous response.
        record_metrics: Optional sink for the page's filter statistics.

    Note: limit is the query size, not result count after filtering.

    """
    exclusive_start_key = _decode_cursor(cursor)

    result = await projects_db.query(
        key_condition={"groupId": group_id},
        index="groupId-createdAt-index",
        limit=limit,
        exclusive_start_key=exclusive_start_key,
    )
    queried = [Project.model_validate(item) for item in result.items]

    projects = [
        project
        for project in queried
        if (
            user_id in project.assigned_user_ids
            or user_id in project.owner_user_id
        )
    ]

    stats = build_filter_stats(
        queried_count=len(queried),
        filtered_count=len(projects),
    )
    if stats.filter_ratio >= FILTER_RATIO_WARNING_THRESHOLD:
        logger.warning(
            "getMyProjects dropped most queried rows: "
            "queried_count=%d filtered_count=%d filter_ratio=%.1f",
            stats.queried_count,
            stats.filtered_count,
            stats.filter_ratio,
        )
    if record_metrics is not None:
        await record_metrics(stats)

    next_cursor = _encode_cursor(result.last_evaluated_key)

    return projects, next_cursor


def build_filter_stats(
    *,
    queried_count: int,
    filtered_count: int,
) -> ProjectFilterStats:
    """Compute how much of a queried page the filter dropped."""
    dropped = queried_count - filtered_count
    ratio = dropped / queried_count * 100 if queried_count else 0.0
    return ProjectFilterStats(
        queried_count=queried_count,
        filtered_count=filtered_count,
        filter_ratio=ratio,
    )


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
