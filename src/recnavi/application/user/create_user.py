# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.

"""Create user use case."""

from recnavi.core.database.base_database import BaseDatabase
from recnavi.core.identity.base_identity_provider import BaseIdentityProvider
from recnavi.core.types.user import User
from recnavi.core.types.user import UserRole
from recnavi.core.user.create_user import create_user


async def create_user_usecase(
    *,
    users_db: BaseDatabase,
    identity_provider: BaseIdentityProvider,
    caller: User,
    email: str,
    user_name: str,
    role: UserRole,
) -> list[User]:
    """Create a user in the caller's group."""
    return await create_user(
        users_db=users_db,
        identity_provider=identity_provider,
        caller=caller,
        email=email,
        user_name=user_name,
        role=role,
    )
