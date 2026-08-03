# Copyright (c) 2025 TOYOTA MOTOR CORPORATION. All rights reserved.
#
# This software is the confidential and proprietary information of
# TOYOTA MOTOR CORPORATION. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# TRUST developer team.

"""example code for TRUST APIs."""

import requests


COGNITO_AUTH_URL = "https://cognito-idp.ap-northeast-1.amazonaws.com/"
COGNITO_CLIENT_ID = "4umhf08uqrekc0nqueaq51rfhh"  # for dev environment.

API_BASE = "https://dev.trust.toyota/apis"  # for dev environment.


def get_token():
    """Get bearer token with ID/PASS."""
    user_name = input("UserName: ")
    password = input("password: ")
    headers = {
        "Content-Type": "application/x-amz-json-1.1",
        "X-Amz-Target": "AWSCognitoIdentityProviderService.InitiateAuth",
    }
    body = {
        "AuthFlow": "USER_PASSWORD_AUTH",
        "ClientId": COGNITO_CLIENT_ID,
        "AuthParameters": {
            "USERNAME": user_name,
            "PASSWORD": password,
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


def call_api(endpoint, *, method="post", body=None):
    """Call api function."""
    token = get_token()
    headers = {
        "Authorization": f"Bearer {token}",
        "Client-Id": COGNITO_CLIENT_ID,
    }
    url = API_BASE + endpoint
    if method.lower() == "post":
        res = requests.post(url, headers=headers, json=body)
    elif method.lower() == "get":
        res = requests.get(url, headers=headers, params=body)
    else:
        raise ValueError("Unsupported method")
    return res.json()


def main():
    """Main code."""
    res = call_api("/greetingMe")
    print(res)


if __name__ == "__main__":
    main()
