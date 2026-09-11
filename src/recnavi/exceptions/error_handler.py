# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.

"""error handler for API."""

import json
import logging
import traceback

import boto3
from fastapi import Request
from fastapi.responses import JSONResponse

from recnavi.config.variables import ENV
from recnavi.core.utils.discord_handler import post_error_discord

from .exceptions import BaseClientExceptionError
from .exceptions import ClientAuthorizationError


ERROR_LOG_BUCKET_NAME = "trust-api-error-log"
ses_client = boto3.client("ses", region_name="ap-northeast-1")

logger = logging.getLogger(__name__)


async def custom_exception_handler(request: Request, exc: Exception):
    """Convert exceptions to common API response payload."""
    x_user = getattr(request.state, "x_user", None)
    func_name = request.scope.get("endpoint", None)
    func_name = getattr(func_name, "__name__", "unknown")
    body_bytes = getattr(request.state, "body", b"")
    try:
        kwargs = json.loads(body_bytes) if body_bytes else {}
    except Exception as parse_err:
        kwargs = {"readRequestBodyError": parse_err.__class__.__name__}

    kwargs["x_user"] = x_user

    if isinstance(exc, ClientAuthorizationError):
        message = str(exc)
        status_code = 403
    elif isinstance(exc, BaseClientExceptionError):
        message = str(exc)
        status_code = 400
    elif isinstance(exc, TypeError):
        message = "Invalid request parameter"
        status_code = 400
    else:
        message = "Unexpected Server Error"
        status_code = 500
        logger.error(
            f"ERROR DETECTED! {traceback.format_exception_only(type(exc), exc)}\n"
            f"environment: {ENV}\n"
            f"traceback:\n{traceback.format_exc()}",
        )
        post_error_discord(
            function_name=func_name,
            e=exc,
            kwargs=kwargs,
            env=ENV,
            additional_message=f"ERROR DETECTED! {traceback.format_exception_only(type(exc), exc)}",
        )

    return JSONResponse(
        status_code=status_code,
        content={"status": "error", "message": message},
    )
