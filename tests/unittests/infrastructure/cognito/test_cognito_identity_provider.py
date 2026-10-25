# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.


"""Cognito adapter request, error and resource contracts."""

from unittest.mock import AsyncMock
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest
from botocore.exceptions import ClientError

from recnavi.exceptions.exceptions import ClientValueError
from recnavi.infrastructure.cognito.cognito_identity_provider import (
    CognitoIdentityProvider,
)


@pytest.mark.asyncio
async def test_cognito_create_duplicate_delete_and_close():
    cognito = MagicMock()
    cognito.admin_create_user = AsyncMock(
        return_value={
            "User": {"Attributes": [{"Name": "sub", "Value": "new-sub"}]},
        },
    )
    cognito.admin_delete_user = AsyncMock()
    cognito.exceptions.UsernameExistsException = ClientError
    context = MagicMock()
    context.__aenter__ = AsyncMock(return_value=cognito)
    context.__aexit__ = AsyncMock(return_value=None)
    session = MagicMock()
    session.client.return_value = context
    with patch(
        "recnavi.infrastructure.cognito.cognito_identity_provider.aioboto3.Session",
        return_value=session,
    ):
        provider = CognitoIdentityProvider(user_pool_id="test-pool")
    assert (
        await provider.create_user(
            email="staff@example.com",
            user_name="Staff",
        )
        == "new-sub"
    )
    cognito.admin_create_user.assert_awaited_once_with(
        UserPoolId="test-pool",
        Username="staff@example.com",
        UserAttributes=[
            {"Name": "email", "Value": "staff@example.com"},
            {"Name": "email_verified", "Value": "true"},
            {"Name": "name", "Value": "Staff"},
        ],
        DesiredDeliveryMediums=["EMAIL"],
    )
    await provider.delete_user(email="staff@example.com")
    cognito.admin_delete_user.assert_awaited_once_with(
        UserPoolId="test-pool",
        Username="staff@example.com",
    )
    cognito.admin_create_user.side_effect = ClientError(
        {"Error": {"Code": "UsernameExistsException", "Message": "exists"}},
        "AdminCreateUser",
    )
    with pytest.raises(ClientValueError, match="already registered") as error:
        await provider.create_user(
            email="staff@example.com",
            user_name="Staff",
        )
    assert isinstance(error.value.__cause__, ClientError)
    assert context.__aexit__.await_count == 3
