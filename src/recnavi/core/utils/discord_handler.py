# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.

"""discord handler"""

import io
import json
import logging
import traceback
from typing import Any

import requests

from recnavi.config.variables import ENV


WEBHOOK_URL = "https://discord.com/api/webhooks/1484011448152752290/_RWHmTjHSHFYbsmrG8Nj9CTHm9eBmozzXMldD6l6LoxAxsWEd7tTVxNw_NCFPgajvhWi"
DISCORD_COLOR = {
    "red": 16711680,
    "yellow": 16776960,
    "green": 3066993,
    "blue": 5793266,
}

ME = "<@1019242781853614111>"
logger = logging.getLogger(__name__)


def post_discord(
    *,
    title: str,
    user_name: str = "Notifire",
    mention: bool = False,
    message: str,
    additional_content: str | None = None,
    color: str | None = None,
    files: dict | None = None,
    webhook_url: str | None = None,
):
    """Post discord
    Args:
        title:
        user_name:
        mention:
        message:
        additional_content:
        color:
        files:
        webhook_url:

    Returns:

    """
    try:
        if webhook_url is None:
            webhook_url = WEBHOOK_URL
        if files is None:
            files = {}
        payload: dict[str, Any] = {
            "username": user_name,
            "content": f"{(ME if mention else '')}\nEnvironment: `{ENV}`\n\n{message}",
        }
        if additional_content:
            payload["embeds"] = [
                {
                    "title": title,
                    "color": DISCORD_COLOR[color],
                    "description": additional_content,
                },
            ]

        response = requests.post(
            webhook_url,
            headers={"User-Agent": "curl/7.64.1"},
            data={"payload_json": json.dumps(payload)},
            files=files,
        )
        logger.info("discord message posted", response.text)
        return response
    except Exception as e:
        logger.error(f"LOG: Failed to send Discord notification. Error: {e}")
        return None, str(e)


def post_notify_discord(
    *,
    title: str,
    message: str,
    additional_content: str | None = None,
    mention: bool = True,
    files: dict | None = None,
) -> None:
    """Sends a general notification to a Discord channel via a webhook.

    Args:
        title (str): The title of the notification embed.
        message (str): The main content of the notification.
        additional_content (str, optional): Additional content to include in the notification. Defaults to "".
        mention (bool, optional): if False: do not mention to dev team
        files: attached file objects: {'file': ('FILENAME', io.BytesIO object),}

    """
    post_discord(
        title=title,
        user_name="PaaRL Notification",
        color="blue",
        mention=mention,
        message=message,
        additional_content=additional_content,
        files=files,
    )


def post_error_discord(
    function_name: str,
    e: Exception,
    kwargs: dict | None = None,
    env: str | None = None,
    additional_message: str | None = None,
) -> None:
    """Send error notification to discord webhook.

    Args:
        function_name:
        e:
        kwargs:
        env:
        additional_message: optional

    """
    if env is None:
        env = ENV
    kwargs_str = json.dumps(
        kwargs,
        ensure_ascii=False,
        indent=4,
        default=lambda o: str(o),
    )
    error_trace = traceback.format_exc()
    attached_file_str = (
        f"# kwargs: {kwargs_str}\n\n# TraceBack:\n{error_trace}"
    )
    trace_file = io.BytesIO()
    trace_file.write(attached_file_str.encode("utf8"))
    trace_file.seek(0)
    files = {
        "file": ("traceback.txt", trace_file),
    }
    message = f"Error detected.\nenvironment: `{env}`\n\nfunction: {function_name}\n{e.__class__.__name__}: {e!s}\n"
    if additional_message:
        message += f"additional_message: {additional_message}\n"

    post_discord(
        title="Detected ERROR in system!",
        user_name="ERROR Alert!",
        mention=True,
        message=message,
        additional_content="Traceback: See the attach file.",
        color="red",
        files=files,
    )
