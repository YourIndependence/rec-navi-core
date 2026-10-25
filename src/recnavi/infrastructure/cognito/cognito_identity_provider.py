# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.

"""Cognito implementation of the identity provider."""

import aioboto3

from recnavi.config.variables import COGNITO_USER_POOL_ID
from recnavi.config.variables import REGION
from recnavi.core.identity.base_identity_provider import BaseIdentityProvider
from recnavi.exceptions.exceptions import ClientValueError


class CognitoIdentityProvider(BaseIdentityProvider):
    """Manage sign-in accounts in an Amazon Cognito user pool."""

    def __init__(self, *, user_pool_id: str = COGNITO_USER_POOL_ID):
        """Initialize with the user pool to manage."""
        self.user_pool_id = user_pool_id
        self.session = aioboto3.Session()

    async def create_user(self, *, email: str, user_name: str) -> str:
        """Create a Cognito user and send the invitation email."""
        async with self.session.client(
            "cognito-idp",
            region_name=REGION,
        ) as cognito:
            try:
                response = await cognito.admin_create_user(
                    UserPoolId=self.user_pool_id,
                    Username=email,
                    UserAttributes=[
                        {"Name": "email", "Value": email},
                        {"Name": "email_verified", "Value": "true"},
                        {"Name": "name", "Value": user_name},
                    ],
                    DesiredDeliveryMediums=["EMAIL"],
                )
            except cognito.exceptions.UsernameExistsException as e:
                raise ClientValueError(
                    "email address is already registered",
                ) from e

        attributes = response["User"]["Attributes"]
        return next(a["Value"] for a in attributes if a["Name"] == "sub")

    async def delete_user(self, *, email: str) -> None:
        """Delete a Cognito user."""
        async with self.session.client(
            "cognito-idp",
            region_name=REGION,
        ) as cognito:
            await cognito.admin_delete_user(
                UserPoolId=self.user_pool_id,
                Username=email,
            )
