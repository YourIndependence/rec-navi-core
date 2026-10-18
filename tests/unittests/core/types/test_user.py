# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.

"""Tests for User type."""

import pytest

from recnavi.core.types.user import User
from recnavi.core.types.user import UserRole
from recnavi.core.types.user import UserSummary


@pytest.mark.parametrize(
    ("user_role", "requested_role", "expected"),
    [
        (UserRole.STAFF, UserRole.STAFF, True),
        (UserRole.STAFF, UserRole.OWNER, False),
        (UserRole.STAFF, UserRole.ADMIN, False),
        (UserRole.OWNER, UserRole.STAFF, True),
        (UserRole.OWNER, UserRole.OWNER, True),
        (UserRole.OWNER, UserRole.ADMIN, False),
        (UserRole.ADMIN, UserRole.STAFF, True),
        (UserRole.ADMIN, UserRole.OWNER, True),
        (UserRole.ADMIN, UserRole.ADMIN, True),
    ],
)
def test_can_act_as_respects_role_hierarchy(
    user_role,
    requested_role,
    expected,
):
    """Test users can act at their role or a lower role."""
    user = User(
        user_id="user-123",
        user_name="Test User",
        role=user_role,
        group_id="group-456",
    )

    assert user.can_act_as(requested_role) is expected


def test_user_summary_serializes_public_fields_with_camel_case() -> None:
    """Public user information has the same identifiers and aliases as User."""
    summary = UserSummary(
        user_id="member",
        user_name="Member",
        role=UserRole.STAFF,
        group_id="group",
        profile_image_uri="s3://media/avatar.png",
    )
    assert summary.model_dump(by_alias=True, mode="json") == {
        "userId": "member",
        "userName": "Member",
        "role": "staff",
        "groupId": "group",
        "profileImageUri": "s3://media/avatar.png",
    }


def test_user_extends_summary_with_private_details_and_authorization() -> None:
    """The full user retains shared fields, private data, and role behavior."""
    user = User(
        user_id="member",
        user_name="Member",
        role=UserRole.OWNER,
        group_id="group",
        email="private@example.com",
        phone_number="123",
    )
    assert isinstance(user, UserSummary)
    assert user.email == "private@example.com"
    assert user.phone_number == "123"
    assert user.group_id == "group"
    assert user.can_act_as(UserRole.STAFF)
    assert user.model_dump(by_alias=True)["userId"] == "member"


def test_user_summary_allows_missing_profile_image() -> None:
    """Members without an avatar keep a nullable image URI."""
    summary = UserSummary(
        user_id="member",
        user_name="Member",
        role=UserRole.STAFF,
        group_id="group",
    )
    assert summary.profile_image_uri is None
    assert summary.model_dump(by_alias=True)["profileImageUri"] is None
