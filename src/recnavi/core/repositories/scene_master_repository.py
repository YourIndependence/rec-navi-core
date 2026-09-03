# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.


"""Scene master repository interface."""

from abc import ABC
from abc import abstractmethod

from recnavi.core.types.scene_master import SceneMaster


class BaseSceneMasterRepository(ABC):
    """Where the scene masters are kept."""

    @abstractmethod
    async def list_all(self) -> list[SceneMaster]:
        """Return every scene master."""

    @abstractmethod
    async def get(self, *, scene_principal: str) -> SceneMaster | None:
        """Return one scene master, or nothing when there is none."""
