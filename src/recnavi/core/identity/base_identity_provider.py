# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.

"""Identity provider abstraction."""

from abc import ABC
from abc import abstractmethod


class BaseIdentityProvider(ABC):
    """Abstract identity provider that owns credentials and sign-in."""

    @abstractmethod
    async def create_user(self, *, email: str, user_name: str) -> str:
        """Create a sign-in account and send an invitation.

        Args:
            email: Email address, also used as the sign-in name.
            user_name: Display name of the account.

        Returns:
            Identifier (sub) of the created account.

        Raises:
            ClientValueError: The email address is already registered.

        """
        pass

    @abstractmethod
    async def delete_user(self, *, email: str) -> None:
        """Delete a sign-in account.

        Args:
            email: Email address of the account to delete.

        """
        pass
