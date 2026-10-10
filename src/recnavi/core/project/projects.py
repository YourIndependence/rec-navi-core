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
from recnavi.core.types.project import ProjectSummary
from recnavi.core.types.user import User
from recnavi.core.types.user import UserRole
from recnavi.exceptions.exceptions import ClientAuthorizationError


async def get_group_projects(
    *,
    projects_db: BaseDatabase,
    user: User,
    limit: int = 20,
    cursor: str | None = None,
) -> tuple[list[ProjectSummary], str | None]:
    """Get every project of the caller's group.

    Args:
        projects_db: Database instance.
        user: Authenticated caller. Must be an owner or an admin.
        limit: Maximum items per page.
        cursor: Opaque pagination cursor from the previous response.

    Raises:
        ClientAuthorizationError: If the caller is neither owner nor admin.

    """
    if user.role not in (UserRole.OWNER, UserRole.ADMIN):
        raise ClientAuthorizationError("Only owners can list group projects")

    projects, next_cursor = await _query_group_projects(
        projects_db=projects_db,
        group_id=user.group_id,
        limit=limit,
        cursor=cursor,
    )
    return [_to_summary(project) for project in projects], next_cursor


async def get_my_projects(
    *,
    projects_db: BaseDatabase,
    user_id: str,
    group_id: str,
    limit: int = 20,
    cursor: str | None = None,
) -> tuple[list[ProjectSummary], str | None]:
    """Get projects the user is assigned to.

    Args:
        projects_db: Database instance.
        user_id: User identifier.
        group_id: User group identifier.
        limit: Number of projects to examine (not the number returned).
        cursor: Opaque pagination cursor from the previous response.

    Note: limit is the query size, not the result count after filtering.
    The result may be shorter than limit, and next_cursor can be non-null
    even when the returned list is empty.

    """
    projects, next_cursor = await _query_group_projects(
        projects_db=projects_db,
        group_id=group_id,
        limit=limit,
        cursor=cursor,
    )
    return [
        _to_summary(project)
        for project in projects
        if user_id in project.assigned_user_ids
    ], next_cursor


async def _query_group_projects(
    *,
    projects_db: BaseDatabase,
    group_id: str,
    limit: int,
    cursor: str | None,
) -> tuple[list[Project], str | None]:
    """Query one page of a group's projects with the next cursor."""
    result = await projects_db.query(
        key_condition={"groupId": group_id},
        index="groupId-createdAt-index",
        limit=limit,
        exclusive_start_key=_decode_cursor(cursor),
    )
    projects = [Project.model_validate(item) for item in result.items]
    return projects, _encode_cursor(result.last_evaluated_key)


def _to_summary(project: Project) -> ProjectSummary:
    """Drop scenes and internal fields from a project."""
    return ProjectSummary.model_validate(
        project.model_dump(
            include=set(ProjectSummary.model_fields),
        ),
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
