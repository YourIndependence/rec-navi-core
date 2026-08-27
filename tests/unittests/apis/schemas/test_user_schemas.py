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
from recnavi.core.types.group_user import GroupUser
from recnavi.core.types.group_user import UserRole


def _response() -> GetMeResponse:
    """A response for a signed-in owner."""
    return GetMeResponse(
        user=GroupUser(
            user_id="7f1c0f2e",
            user_name="Koki Ueno",
            role=UserRole.OWNER,
        ),
        group_id="grp_sushi_taro",
    )


def test_serializes_in_camel_case():
    """The wire format is camelCase, the Python one is snake_case."""
    body = _response().model_dump(by_alias=True)

    assert body == {
        "status": "ok",
        "message": None,
        "user": {
            "userId": "7f1c0f2e",
            "userName": "Koki Ueno",
            "role": "owner",
        },
        "groupId": "grp_sushi_taro",
    }


def test_defaults_to_a_successful_status():
    """A caller never has to set the status by hand."""
    assert _response().status == "ok"
