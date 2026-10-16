from io import BytesIO
from unittest.mock import patch

from recnavi.core.utils import discord_handler


def test_post_notify_discord_delegates_to_post_discord():
    with patch.object(discord_handler, "_post_discord") as post_discord:
        discord_handler.post_notify_discord(
            title="Deployment",
            message="Deployment completed",
            additional_content="Version 1.2.3",
            mention=False,
        )

    post_discord.assert_called_once_with(
        title="Deployment",
        user_name="Notification",
        color="blue",
        mention=False,
        message="Deployment completed",
        additional_content="Version 1.2.3",
        files=None,
    )


def test_post_error_discord_delegates_error_details_and_trace_file():
    error = ValueError("invalid input")

    with patch.object(discord_handler, "_post_discord") as post_discord:
        discord_handler.post_error_discord(
            "process_request",
            error,
            kwargs={"request_id": "req-123"},
            env="CI",
            additional_message="Retry required",
        )

    post_discord.assert_called_once()
    call = post_discord.call_args.kwargs
    assert call["title"] == "Detected ERROR in system!"
    assert call["user_name"] == "ERROR Alert!"
    assert call["mention"] is True
    assert call["color"] == "red"
    assert call["message"] == (
        "Error detected.\n"
        "environment: `CI`\n\n"
        "function: process_request\n"
        "ValueError: invalid input\n"
        "additional_message: Retry required\n"
    )
    assert call["additional_content"] == "Traceback: See the attach file."
    file_name, trace_file = call["files"]["file"]
    assert file_name == "traceback.txt"
    assert isinstance(trace_file, BytesIO)
