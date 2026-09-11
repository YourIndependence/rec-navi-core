# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.

import pytest

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
