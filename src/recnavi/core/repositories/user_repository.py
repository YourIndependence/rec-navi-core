# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.


"""User repository interface."""

from abc import ABC
from abc import abstractmethod

from recnavi.core.types.group_user import GroupUser


class BaseUserRepository(ABC):
    """Where the users are kept."""

    @abstractmethod
    async def get(self, *, user_id: str) -> GroupUser | None:
        """Return one user, or nothing when there is no record."""
