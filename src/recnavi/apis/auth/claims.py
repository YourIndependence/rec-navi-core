# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.

"""Cognito claims to domain user."""

from collections.abc import Mapping
from collections.abc import Sequence

from recnavi.core.types.authenticated_user import AuthenticatedUser
from recnavi.core.types.group_user import GroupUser
from recnavi.core.types.group_user import UserRole
from recnavi.exceptions.exceptions import ClientAuthorizationError


USER_ID_CLAIM = "sub"
USER_NAME_CLAIM = "name"
ROLE_CLAIM = "custom:role"
GROUPS_CLAIM = "cognito:groups"


def build_authenticated_user(
    *,
    claims: Mapping[str, object],
) -> AuthenticatedUser:
    """Map verified Cognito claims onto the domain user."""
    return AuthenticatedUser(
        user=GroupUser(
            user_id=_read_text(claims=claims, name=USER_ID_CLAIM),
            user_name=_read_text(claims=claims, name=USER_NAME_CLAIM),
            role=_read_role(claims=claims),
        ),
        group_id=_read_group_id(claims=claims),
    )


def _read_text(*, claims: Mapping[str, object], name: str) -> str:
    """Read a claim that must carry a non-blank string."""
    value = claims.get(name)
    if not isinstance(value, str) or not value.strip():
        raise ClientAuthorizationError(
            f"The account is missing the '{name}' attribute.",
        )
    return value.strip()


def _read_role(*, claims: Mapping[str, object]) -> UserRole:
    """Read the role, refusing anything we do not define."""
    value = _read_text(claims=claims, name=ROLE_CLAIM)
    try:
        return UserRole(value)
    except ValueError as e:
        raise ClientAuthorizationError(
            f"'{value}' is not a role this service grants.",
        ) from e


def _read_group_id(*, claims: Mapping[str, object]) -> str:
    """Read the single group the user belongs to."""
    groups = claims.get(GROUPS_CLAIM)
    if not isinstance(groups, Sequence) or isinstance(groups, str):
        raise ClientAuthorizationError(
            "The account is missing the 'cognito:groups' attribute.",
        )
    if len(groups) != 1:
        raise ClientAuthorizationError(
            "The account must belong to exactly one group, "
            f"but it belongs to {len(groups)}.",
        )
    group_id = groups[0]
    if not isinstance(group_id, str) or not group_id.strip():
        raise ClientAuthorizationError(
            "The group the account belongs to has no name.",
        )
    return group_id.strip()
