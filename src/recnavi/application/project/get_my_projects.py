"""List the projects assigned to the caller."""

from recnavi.core.database.base_database import BaseDatabase
from recnavi.core.project.projects import get_my_projects
from recnavi.core.types.project import ProjectSummary


async def get_my_projects_usecase(
    *,
    projects_db: BaseDatabase,
    user_id: str,
    group_id: str,
    limit: int,
    cursor: str | None,
) -> tuple[list[ProjectSummary], str | None]:
    """List the projects the caller is assigned to.

    Returns:
        Tuple of (projects, next_cursor). limit is the number of projects
        examined, so the list may be shorter and next_cursor can be set
        even when the list is empty.

    """
    return await get_my_projects(
        projects_db=projects_db,
        user_id=user_id,
        group_id=group_id,
        limit=limit,
        cursor=cursor,
    )
