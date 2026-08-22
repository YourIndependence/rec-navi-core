# Copyright (c) 2025 TOYOTA MOTOR CORPORATION. All rights reserved.
#
# This software is the confidential and proprietary information of
# TOYOTA MOTOR CORPORATION. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# TRUST developer team.

"""test utils"""

from __future__ import annotations

import json
import os
import random
import string
from typing import TYPE_CHECKING

import requests

from recnavi.infrastructure.external_clients.aws_clients import (
    get_secret_client,
)


if TYPE_CHECKING:
    from recnavi.core.agents.agent_registry import AgentRegistry


def get_random_string(k=1):
    """Get random string"""
    return "".join(random.choices(string.ascii_letters + string.digits, k=k))


def get_test_token():
    """Get test token"""
    headers = {
        "Content-Type": "application/x-amz-json-1.1",
        "X-Amz-Target": "AWSCognitoIdentityProviderService.InitiateAuth",
    }
    body = {
        "AuthFlow": "USER_PASSWORD_AUTH",
        "ClientId": TEST_COGNITO_CLIENT_ID,
        "AuthParameters": {
            "USERNAME": TEST_USERNAME,
            "PASSWORD": TEST_USER_PASSWORD,
        },
    }
    res = requests.post(COGNITO_AUTH_URL, headers=headers, json=body)
    if res.status_code != 200:
        raise RuntimeError("Failed Auth error")
    res = res.json()
    access_token = res.get("AuthenticationResult", {}).get("AccessToken")
    if not access_token:
        raise RuntimeError("AccessToken is not provided.")
    return access_token
