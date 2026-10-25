# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.

"""Create user domain logic."""

from recnavi.core.database.base_database import BaseDatabase
from recnavi.core.identity.base_identity_provider import BaseIdentityProvider
from recnavi.core.types.user import User
from recnavi.core.types.user import UserRole
from recnavi.exceptions.exceptions import ClientAuthorizationError
from recnavi.exceptions.exceptions import ClientValueError


async def create_user(
    *,
    users_db: BaseDatabase,
    identity_provider: BaseIdentityProvider,
    caller: User,
    email: str,
    user_name: str,
    role: UserRole,
) -> list[User]:
    """Create a user in the caller's group and return the group's users.

    The account is created in the identity provider first, then recorded in
    the users table. If the record cannot be written, the account is deleted
    again so that no half-created user remains.
    """
    if caller.role != UserRole.OWNER:
        raise ClientAuthorizationError("forbidden")

    if role == UserRole.ADMIN:
        raise ClientValueError(
            "role must be 'owner' or 'staff'",
        )

    user_id = await identity_provider.create_user(
        email=email,
        user_name=user_name,
    )

    user = User(
        user_id=user_id,
        user_name=user_name,
        role=role,
        group_id=caller.group_id,
        email=email,
    )

    try:
        await users_db.put_item(
            user.model_dump(by_alias=True, exclude_none=True),
        )
    except Exception:
        await identity_provider.delete_user(email=email)
        raise

    return await list_group_users(users_db=users_db, group_id=caller.group_id)


async def list_group_users(
    *,
    users_db: BaseDatabase,
    group_id: str,
) -> list[User]:
    """List the users who belong to a group."""
    result = await users_db.scan(filter_expression={"groupId": group_id})
    return [User.model_validate(item) for item in result.items]
