# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.

"""Tests for notify_project_submitted."""

import logging

import pytest

from recnavi.core.project.notify_project_submitted import build_review_url
from recnavi.core.project.notify_project_submitted import (
    notify_project_submitted,
)
from recnavi.core.types.project_view import ProjectView
from recnavi.core.types.user import User
from recnavi.core.types.user import UserRole
from tests.mockups.mock_database import MockDatabase
from tests.mockups.mock_notifier import MockNotifier


def _project() -> ProjectView:
    return ProjectView.model_validate(
        {
            "projectId": "proj-1",
            "groupId": "group-1",
            "projectName": "Spring Menu",
            "ownerUserId": "owner-1",
            "createdAt": "2026-09-01T00:00:00Z",
            "updatedAt": "2026-09-01T00:00:00Z",
            "description": "",
            "status": "submitted",
            "assignedUserIds": ["staff-1"],
            "scenes": [],
        },
    )


def _staff() -> User:
    return User(
        user_id="staff-1",
        user_name="Hanako",
        role=UserRole.STAFF,
        group_id="group-1",
    )


def _users_db(email: str | None = "owner@example.com") -> MockDatabase:
    owner = {
        "userId": "owner-1",
        "userName": "Owner",
        "role": "owner",
        "groupId": "group-1",
    }
    if email:
        owner["email"] = email
    return MockDatabase(initial_items=[owner])


def test_build_review_url_joins_base_url_and_project_id():
    """Test the review link has no duplicated slash."""
    url = build_review_url(
        base_url="http://localhost:5173/",
        project_id="p1",
    )

    assert url == "http://localhost:5173/projects/p1/review"


@pytest.mark.asyncio
async def test_notify_sends_project_staff_and_link_to_owner(caplog):
    """Test the owner is emailed the project, the staff name and the link."""
    notifier = MockNotifier()

    with caplog.at_level(logging.INFO):
        sent = await notify_project_submitted(
            users_db=_users_db(),
            notifier=notifier,
            project=_project(),
            submitter=_staff(),
            base_url="http://localhost:5173",
        )

    assert sent is True
    assert notifier.sent == [
        {
            "to_email": "owner@example.com",
            "project_name": "Spring Menu",
            "staff_name": "Hanako",
            "review_url": "http://localhost:5173/projects/proj-1/review",
        },
    ]
    assert "owner notification sent" in caplog.text


@pytest.mark.asyncio
async def test_notify_returns_false_and_logs_when_send_fails(caplog):
    """Test a delivery failure is logged and not raised."""
    notifier = MockNotifier(fail=True)

    with caplog.at_level(logging.ERROR):
        sent = await notify_project_submitted(
            users_db=_users_db(),
            notifier=notifier,
            project=_project(),
            submitter=_staff(),
            base_url="http://localhost:5173",
        )

    assert sent is False
    assert "owner notification failed" in caplog.text


@pytest.mark.asyncio
@pytest.mark.parametrize("users_db", [_users_db(email=None), MockDatabase()])
async def test_notify_skips_when_owner_has_no_email(users_db, caplog):
    """Test a missing owner record or address skips the send with a warning."""
    notifier = MockNotifier()

    with caplog.at_level(logging.WARNING):
        sent = await notify_project_submitted(
            users_db=users_db,
            notifier=notifier,
            project=_project(),
            submitter=_staff(),
            base_url="http://localhost:5173",
        )

    assert sent is False
    assert notifier.sent == []
    assert "owner notification skipped" in caplog.text
