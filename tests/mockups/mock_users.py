# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.

import pytest

from recnavi.core.types.authenticated_user import AuthenticatedUser
from recnavi.core.types.group_user import GroupUser
from recnavi.core.types.group_user import UserRole
from recnavi.core.types.x_user import XUser


@pytest.fixture
def mock_x_user():
    return get_mock_x_user()


def get_mock_x_user() -> XUser:
    """Get x user
    `mock_verify_user` merge to here!
    """
    return XUser.model_validate(
        get_mock_user(),
    )


def get_mock_user():
    """Get mock user"""
    return {
        "id": 1,
        "email": "test.mail@mail.example.com",
        "role": "admin",
    }


@pytest.fixture
def mock_authenticated_user():
    return get_mock_authenticated_user()


def get_mock_authenticated_user() -> AuthenticatedUser:
    """Get the caller behind a request in tests"""
    return AuthenticatedUser(
        user=GroupUser(
            user_id="7f1c0f2e-0a3d-4a1b-9c2e-2b7a6d5e4f30",
            user_name="Koki Ueno",
            role=UserRole.OWNER,
        ),
        group_id="grp_sushi_taro",
    )
