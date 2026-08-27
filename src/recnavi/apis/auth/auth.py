# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.

"""Authorization verify."""

import boto3
import httpx
from fastapi import HTTPException
from fastapi import Request
from fastapi import status
from jose import jwt
from jose.exceptions import ExpiredSignatureError
from jose.exceptions import JWTError

from recnavi.apis.auth.claims import build_authenticated_user
from recnavi.config.variables import COGNITO_CLIENT_ID
from recnavi.config.variables import COGNITO_USER_POOL_ID
from recnavi.config.variables import REGION
from recnavi.core.types.authenticated_user import AuthenticatedUser
from recnavi.core.types.x_user import XUser
from recnavi.exceptions.exceptions import ClientAuthorizationError
from recnavi.exceptions.exceptions import ClientPermissionError


client = boto3.client("cognito-idp", region_name="ap-northeast-1")
COGNITO_JWK_URL = f"https://cognito-idp.{REGION}.amazonaws.com/{COGNITO_USER_POOL_ID}/.well-known/jwks.json"


async def verify_user(request: Request) -> XUser:
    """Verify user"""
    try:
        x_user = await get_verified_user(request)
        request.state.x_user = x_user
        return x_user

    except ClientPermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e),
        ) from e


async def get_authenticated_user(request: Request) -> AuthenticatedUser:
    """Resolve the signed-in user, or refuse the request."""
    try:
        claims = await decode_token(request)
    except ClientPermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
        ) from e

    try:
        authenticated_user = build_authenticated_user(claims=claims)
    except ClientAuthorizationError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e),
        ) from e

    request.state.authenticated_user = authenticated_user
    return authenticated_user


async def get_verified_user(request: Request) -> XUser:
    """Verify jwe token"""
    payload = await decode_token(request)
    return XUser(
        id=payload.get("id"),
        email=payload.get("email"),
    )


async def decode_token(request: Request) -> dict[str, object]:
    """Verify the bearer token and return its claims."""
    authorization = request.headers.get("authorization")
    client_id = request.headers.get("client-Id", COGNITO_CLIENT_ID)
    if not authorization:
        raise ClientPermissionError("Authorization header is required.")
    if not authorization.startswith("Bearer "):
        raise ClientPermissionError(
            "Authorization header must start with 'Bearer '",
        )
    token = authorization.split(" ")[1]

    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(10.0)) as clt:
            response = await clt.get(COGNITO_JWK_URL)
            response.raise_for_status()
        jwks = response.json()["keys"]
        headers = jwt.get_unverified_header(token)
        kid = headers.get("kid")
        key = next((key for key in jwks if key["kid"] == kid), None)

        if key is None:
            raise ClientPermissionError("Invalid token")

        payload = jwt.decode(
            token,
            key,
            audience=client_id,
            issuer=f"https://cognito-idp.{REGION}.amazonaws.com/{COGNITO_USER_POOL_ID}",
            options={"verify_at_hash": False},
        )

        return payload

    except httpx.HTTPError as e:
        raise JWTError(f"Failed to fetch JWKs: {e!s}") from e
    except ExpiredSignatureError as e:
        raise ClientPermissionError("Token signature has expired.") from e
    except JWTError as e:
        raise ClientPermissionError("Token verification failed.") from e
    except Exception as e:
        raise e
