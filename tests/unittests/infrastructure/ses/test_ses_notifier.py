# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.

"""Tests for SesNotifier."""

from unittest.mock import AsyncMock
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest
from botocore.exceptions import ClientError

from recnavi.exceptions.exceptions import NotificationSendError
from recnavi.infrastructure.ses.ses_notifier import SesNotifier


MODULE = "recnavi.infrastructure.ses.ses_notifier"


def _session_with(ses: AsyncMock) -> MagicMock:
    client_cm = MagicMock()
    client_cm.__aenter__ = AsyncMock(return_value=ses)
    client_cm.__aexit__ = AsyncMock(return_value=None)
    session = MagicMock()
    session.client.return_value = client_cm
    return session


async def _send(notifier: SesNotifier) -> None:
    await notifier.send_project_submitted(
        to_email="owner@example.com",
        project_name="Spring Menu",
        staff_name="Hanako",
        review_url="http://localhost:5173/project/p1",
    )


@pytest.mark.asyncio
async def test_send_project_submitted_sends_email_through_ses():
    """Test the email carries recipient, project, staff and link."""
    ses = AsyncMock()
    with patch(f"{MODULE}.aioboto3.Session", return_value=_session_with(ses)):
        await _send(SesNotifier(sender_email="no-reply@example.com"))

    kwargs = ses.send_email.await_args.kwargs
    assert kwargs["FromEmailAddress"] == "no-reply@example.com"
    assert kwargs["Destination"] == {"ToAddresses": ["owner@example.com"]}
    simple = kwargs["Content"]["Simple"]
    assert "Spring Menu" in simple["Subject"]["Data"]
    body = simple["Body"]["Text"]["Data"]
    assert "Hanako" in body
    assert "http://localhost:5173/project/p1" in body


@pytest.mark.asyncio
async def test_send_project_submitted_wraps_ses_errors():
    """Test an SES failure becomes NotificationSendError."""
    ses = AsyncMock()
    ses.send_email.side_effect = ClientError(
        {"Error": {"Code": "MessageRejected", "Message": "no"}},
        "SendEmail",
    )
    with patch(f"{MODULE}.aioboto3.Session", return_value=_session_with(ses)):
        with pytest.raises(NotificationSendError):
            await _send(SesNotifier(sender_email="no-reply@example.com"))
