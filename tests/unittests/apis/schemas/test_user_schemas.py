# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.

"""Unit tests for the user API schemas."""

from recnavi.apis.schemas.user_schemas import GetMeResponse
from tests.mockups.mock_user_repository import get_mock_group_user


def test_serializes_in_camel_case():
    """The wire format is camelCase, the Python one is snake_case."""
    body = GetMeResponse.from_group_user(
        get_mock_group_user(),
    ).model_dump(by_alias=True)

    assert body == {
        "status": "ok",
        "message": None,
        "user": {
            "userId": "7f1c0f2e-0a3d-4a1b-9c2e-2b7a6d5e4f30",
            "userName": "Koki Ueno",
            "role": "owner",
        },
        "groupId": "grp_sushi_taro",
    }


def test_names_the_tenant_once():
    """The group is not repeated inside the member."""
    body = GetMeResponse.from_group_user(
        get_mock_group_user(),
    ).model_dump(by_alias=True)

    assert "groupId" not in body["user"]


def test_defaults_to_a_successful_status():
    """A caller never has to set the status by hand."""
    response = GetMeResponse.from_group_user(get_mock_group_user())

    assert response.status == "ok"
