# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.

"""Amazon SES implementation of the notifier."""

import aioboto3
from botocore.config import Config
from botocore.exceptions import BotoCoreError
from botocore.exceptions import ClientError

from recnavi.config.variables import REGION
from recnavi.config.variables import SES_SENDER_EMAIL
from recnavi.core.notification.base_notifier import BaseNotifier
from recnavi.exceptions.exceptions import NotificationSendError


RETRY_CONFIG = Config(retries={"max_attempts": 3, "mode": "standard"})


class SesNotifier(BaseNotifier):
    """Send notification emails through Amazon SES."""

    def __init__(self, *, sender_email: str = SES_SENDER_EMAIL):
        """Initialize with the verified sender address."""
        self.sender_email = sender_email
        self.session = aioboto3.Session()

    async def send_project_submitted(
        self,
        *,
        to_email: str,
        project_name: str,
        staff_name: str,
        review_url: str,
    ) -> None:
        """Send the project-submitted email, retrying transient failures."""
        subject = f"[REC NAVI] Project submitted: {project_name}"
        body = (
            f"{staff_name} has submitted the project "
            f'"{project_name}" for your review.\n\n'
            f"Review it here: {review_url}\n"
        )
        try:
            async with self.session.client(
                "sesv2",
                region_name=REGION,
                config=RETRY_CONFIG,
            ) as ses:
                await ses.send_email(
                    FromEmailAddress=self.sender_email,
                    Destination={"ToAddresses": [to_email]},
                    Content={
                        "Simple": {
                            "Subject": {"Data": subject, "Charset": "UTF-8"},
                            "Body": {
                                "Text": {"Data": body, "Charset": "UTF-8"},
                            },
                        },
                    },
                )
        except (ClientError, BotoCoreError) as e:
            raise NotificationSendError(
                "failed to send project submitted email",
            ) from e
