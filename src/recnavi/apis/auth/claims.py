# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.


"""Cognito claims."""

from collections.abc import Mapping

from recnavi.exceptions.exceptions import ClientAuthorizationError


USER_ID_CLAIM = "sub"


def read_user_id(*, claims: Mapping[str, object]) -> str:
    """Read the identifier Cognito minted for this user.

    This is the only claim the application reads. What the user may do
    and which tenant they belong to are stored in the users table, so a
    change takes effect on the next request rather than on the next
    sign-in.
    """
    value = claims.get(USER_ID_CLAIM)
    if not isinstance(value, str) or not value.strip():
        raise ClientAuthorizationError(
            f"The token carries no '{USER_ID_CLAIM}'.",
        )
    return value.strip()
