# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.

"""Notifier abstraction."""

from abc import ABC
from abc import abstractmethod


class BaseNotifier(ABC):
    """Abstract notifier that delivers messages to users."""

    @abstractmethod
    async def send_project_submitted(
        self,
        *,
        to_email: str,
        project_name: str,
        staff_name: str,
        review_url: str,
    ) -> None:
        """Tell an owner that a project was submitted for review.

        Args:
            to_email: Address of the owner.
            project_name: Name of the submitted project.
            staff_name: Name of the staff member who submitted it.
            review_url: Link to the review screen.

        Raises:
            NotificationSendError: The message could not be delivered.

        """
        pass
