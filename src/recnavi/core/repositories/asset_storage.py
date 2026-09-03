# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.


"""Asset storage interface."""

from abc import ABC
from abc import abstractmethod


class BaseAssetStorage(ABC):
    """Where the application assets are kept."""

    @abstractmethod
    async def read(self, *, key: str) -> bytes | None:
        """Return the stored bytes, or nothing when there is no object."""
