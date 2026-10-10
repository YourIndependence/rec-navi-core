"""List every project of the caller's group."""

from recnavi.core.database.base_database import BaseDatabase
from recnavi.core.project.projects import get_group_projects
from recnavi.core.types.project import ProjectSummary
from recnavi.core.types.user import User


async def get_projects_usecase(
    *,
    projects_db: BaseDatabase,
    user: User,
    limit: int,
    cursor: str | None,
) -> tuple[list[ProjectSummary], str | None]:
    """List all projects of the caller's group.

    Returns:
        Tuple of (projects, next_cursor). next_cursor is None on the last page.

    """
    return await get_group_projects(
        projects_db=projects_db,
        user=user,
        limit=limit,
        cursor=cursor,
    )
