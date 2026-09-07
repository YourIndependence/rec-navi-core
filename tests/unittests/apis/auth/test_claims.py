# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.

"""Unit tests for the Cognito claim reader."""

import pytest

from recnavi.apis.auth.claims import read_user_id
from recnavi.exceptions.exceptions import ClientAuthorizationError


def test_reads_the_identifier():
    """The identifier Cognito mints is the one the app stores."""
    assert read_user_id(claims={"sub": "7f1c0f2e"}) == "7f1c0f2e"


def test_trims_the_identifier():
    """A claim padded with spaces still names the same user."""
    assert read_user_id(claims={"sub": "  7f1c0f2e  "}) == "7f1c0f2e"


@pytest.mark.parametrize(
    "claims",
    [
        {},
        {"sub": ""},
        {"sub": "   "},
        {"sub": 1},
        {"id": "7f1c0f2e"},
    ],
)
def test_refuses_a_token_that_names_nobody(claims):
    """Without sub there is no user to look up."""
    with pytest.raises(ClientAuthorizationError):
        read_user_id(claims=claims)
