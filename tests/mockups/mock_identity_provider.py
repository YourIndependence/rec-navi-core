# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.

"""Mock identity provider for unit testing."""

from uuid import uuid4

from recnavi.core.identity.base_identity_provider import BaseIdentityProvider
from recnavi.exceptions.exceptions import ClientValueError


class MockIdentityProvider(BaseIdentityProvider):
    """In-memory identity provider for unit testing."""

    def __init__(self) -> None:
        """Initialize with no registered accounts."""
        self.accounts: dict[str, str] = {}

    async def create_user(self, *, email: str, user_name: str) -> str:
        """Register an account and return a generated sub."""
        if email in self.accounts:
            raise ClientValueError("email address is already registered")
        user_id = str(uuid4())
        self.accounts[email] = user_id
        return user_id

    async def delete_user(self, *, email: str) -> None:
        """Remove an account."""
        self.accounts.pop(email, None)
