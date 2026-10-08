# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.

"""Mock notifier for unit testing."""

from recnavi.core.notification.base_notifier import BaseNotifier
from recnavi.exceptions.exceptions import NotificationSendError


class MockNotifier(BaseNotifier):
    """In-memory notifier that records what would have been sent."""

    def __init__(self, *, fail: bool = False) -> None:
        """Initialize, optionally failing every send."""
        self.fail = fail
        self.sent: list[dict[str, str]] = []

    async def send_project_submitted(
        self,
        *,
        to_email: str,
        project_name: str,
        staff_name: str,
        review_url: str,
    ) -> None:
        """Record the message or raise when configured to fail."""
        if self.fail:
            raise NotificationSendError("mock send failure")
        self.sent.append(
            {
                "to_email": to_email,
                "project_name": project_name,
                "staff_name": staff_name,
                "review_url": review_url,
            },
        )
