# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.

import pytest

from recnavi.core.repositories.user_repository import BaseUserRepository
from recnavi.core.types.group_user import GroupUser
from recnavi.core.types.group_user import UserRole


class MockUserRepository(BaseUserRepository):
    """Users held in memory"""

    def __init__(self, users: list[GroupUser] | None = None) -> None:
        self.users = get_mock_users() if users is None else users

    async def get(self, *, user_id: str) -> GroupUser | None:
        for user in self.users:
            if user.user_id == user_id:
                return user
        return None


@pytest.fixture
def mock_user_repository():
    return MockUserRepository()


def get_mock_users() -> list[GroupUser]:
    """Get the users used across tests"""
    return [
        get_mock_group_user(),
        GroupUser(
            user_id="9a2d1b3c",
            user_name="Hanako Sato",
            role=UserRole.STAFF,
            group_id="grp_sushi_taro",
        ),
    ]


def get_mock_group_user() -> GroupUser:
    """Get the signed-in user used across tests"""
    return GroupUser(
        user_id="7f1c0f2e-0a3d-4a1b-9c2e-2b7a6d5e4f30",
        user_name="Koki Ueno",
        role=UserRole.OWNER,
        group_id="grp_sushi_taro",
    )
