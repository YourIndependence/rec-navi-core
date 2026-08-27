# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.

"""Unit tests for the Cognito claim mapper."""

import pytest

from recnavi.apis.auth.claims import build_authenticated_user
from recnavi.core.types.group_user import UserRole
from recnavi.exceptions.exceptions import ClientAuthorizationError


def _valid_claims() -> dict[str, object]:
    """Claims of a correctly configured account."""
    return {
        "sub": "7f1c0f2e-0a3d-4a1b-9c2e-2b7a6d5e4f30",
        "name": "Koki Ueno",
        "custom:role": "owner",
        "cognito:groups": ["grp_sushi_taro"],
    }


def test_maps_every_claim():
    """A complete token yields the user and the tenant."""
    caller = build_authenticated_user(claims=_valid_claims())

    assert caller.user.user_id == "7f1c0f2e-0a3d-4a1b-9c2e-2b7a6d5e4f30"
    assert caller.user.user_name == "Koki Ueno"
    assert caller.user.role is UserRole.OWNER
    assert caller.group_id == "grp_sushi_taro"


@pytest.mark.parametrize(
    "role",
    ["admin", "owner", "staff"],
)
def test_accepts_every_known_role(role: str):
    """Each of the three roles maps onto the enumeration."""
    claims = _valid_claims()
    claims["custom:role"] = role

    caller = build_authenticated_user(claims=claims)

    assert caller.user.role == role


def test_rejects_unknown_role():
    """A role outside the three we define is refused."""
    claims = _valid_claims()
    claims["custom:role"] = "guest"

    with pytest.raises(ClientAuthorizationError):
        build_authenticated_user(claims=claims)


@pytest.mark.parametrize(
    "missing",
    ["sub", "name", "custom:role", "cognito:groups"],
)
def test_rejects_missing_claim(missing: str):
    """Every claim we read is mandatory."""
    claims = _valid_claims()
    del claims[missing]

    with pytest.raises(ClientAuthorizationError):
        build_authenticated_user(claims=claims)


def test_rejects_account_in_no_group():
    """An account outside every tenant cannot be served."""
    claims = _valid_claims()
    claims["cognito:groups"] = []

    with pytest.raises(ClientAuthorizationError):
        build_authenticated_user(claims=claims)


def test_rejects_account_in_two_groups():
    """One user belongs to exactly one tenant."""
    claims = _valid_claims()
    claims["cognito:groups"] = ["grp_sushi_taro", "grp_hotel_umi"]

    with pytest.raises(ClientAuthorizationError):
        build_authenticated_user(claims=claims)


def test_rejects_blank_claim():
    """A present but empty claim is as unusable as a missing one."""
    claims = _valid_claims()
    claims["name"] = "   "

    with pytest.raises(ClientAuthorizationError):
        build_authenticated_user(claims=claims)
