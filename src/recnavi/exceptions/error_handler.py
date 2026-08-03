"""error handler for API."""

import asyncio
import json
import logging
import traceback
from collections.abc import Callable
from datetime import datetime
from typing import Any

import boto3
from fastapi import Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from recnavi.config.variables import ENV
from recnavi.config.variables import TRUST_ALERT_MAIL_TABLE  # TODO: Change to hook discord or something...
from recnavi.config.variables import s3

from .exceptions import BaseClientExceptionError
from .exceptions import ClientAuthorizationError


ERROR_LOG_BUCKET_NAME = "trust-api-error-log"
ses_client = boto3.client("ses", region_name="ap-northeast-1")

logger = logging.getLogger(__name__)


async def custom_exception_handler(request: Request, exc: Exception):
    """Error handler."""
    x_user = getattr(request.state, "x_user", None)
    func_name = request.scope.get("endpoint", None)
    func_name = getattr(func_name, "__name__", "unknown")
    body_bytes = getattr(request.state, "body", b"")
    try:
        kwargs = json.loads(body_bytes) if body_bytes else {}
    except Exception as e:
        kwargs = {"readRequestBodyError": e.__class__.__name__}

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
            f"ERROR DETECTED!  {traceback.format_exception_only(type(exc), exc)}\n"
            f"function: {func_name}\n"
            f"traceback:\n{traceback.format_exc()}",
        )
        try:
            log_s3(func_name, exc, kwargs)
        except Exception as log_err:
            logger.error(f"Failed to upload log to S3: {log_err}")

        await send_error_alert(func_name, exc, kwargs=kwargs)

    return JSONResponse(
        status_code=status_code,
        content={
            "status": "ERROR",
            "message": message,
        },
    )


def log_s3(func: Callable[..., Any], e, kwargs):
    """Log s3."""
    messages = traceback.format_exception_only(type(e), e)
    e_obj = {
        "functionName": func.__name__ if hasattr(func, "__name__") else str(func),
        "environment": ENV,
        "timestamp": datetime.now().isoformat(),
        "kwargs": kwargs,
        "message": f"{messages}",
        "traceback": f"{traceback.format_exc()}",
    }
    for k, v in e_obj.items():
        logger.debug(f"{k}\n{v}\n")
    s3_key = f"ERROR_LOG_{datetime.now().isoformat()}.json"
    s3.put_object(
        Bucket=ERROR_LOG_BUCKET_NAME,
        Key=s3_key,
        Body=json.dumps(e_obj, ensure_ascii=False, indent=4, default=_tojson),
        ContentType="application/json",
    )


async def send_error_alert(
    func: Callable[..., Any] | str,
    e,
    *,
    args=None,
    kwargs=None,
    task_id=None,
):
    """Send alert email."""
    try:
        if args is None:
            args = []
        if kwargs is None:
            kwargs = {}
        messages = traceback.format_exception_only(type(e), e)
        func_name = func.__name__ if callable(func) else str(func)
        e_obj = {
            "message": f"{messages}",
            "functionName": func_name,
            "environment": ENV,
            "timestamp": datetime.now().isoformat(),
            "args": args,
            "kwargs": kwargs,
        }

        logger.error(f"ERROR DETECTED!  {traceback.format_exc()}\n")
        await send_notice(
            message=f"{json.dumps(e_obj, ensure_ascii=False, indent=4, default=_tojson)}\n\ntraceback:\n{traceback.format_exc()}",
            task_id=task_id,
        )
    except Exception as notify_err:
        logger.error(f"Fail to send error alert!: {notify_err!r}\n{traceback.format_exc()}\n")


async def send_notice(
    message: str,
    subject: str | None = None,
    to_mail_list: list | None = None,
    task_id: str | None = None,
):
    """Send mail asynchronously."""
    try:
        await asyncio.to_thread(
            _send_notice_sync,
            message,
            subject,
            to_mail_list,
        )
    except Exception as notify_err:
        if task_id:
            error_msg = f"Failed to send alert email: {notify_err}"
        else:
            error_msg = f"Failed to send alert email for task {task_id}: {notify_err}"
        logger.error(error_msg)


def _send_notice_sync(
    message: str,
    subject: str | None = None,
    to_mail_list: list | None = None,
):
    """Send mail."""
    if subject is None:
        subject = f"TRUST alert detected! env: {ENV}"
    if ENV in ["LOCAL_CONTAINER", "CI"]:
        logging.info(
            f"email notice sent, ToAddresses: {to_mail_list}, Subject: {subject}, Text: {message}",
        )
        return None
    if to_mail_list is None:
        to_mail_list = TRUST_ALERT_MAIL_TABLE.get_item(Key={"toEmail": "toEmail"}).get("Item", {}).get("address", [])
    return ses_client.send_email(
        Source="alert@mail.recnavitoyota",
        Destination={"ToAddresses": to_mail_list},
        Message={
            "Subject": {"Data": subject},
            "Body": {
                "Text": {
                    "Data": message,
                },
            },
        },
    )


def _tojson(x):
    if isinstance(x, BaseModel):
        return dict(x)
    elif isinstance(x, Request):
        return x.json()
    return None
