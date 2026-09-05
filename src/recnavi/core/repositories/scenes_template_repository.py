# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.


"""Scenes template repository interface."""

from abc import ABC
from abc import abstractmethod

from recnavi.core.types.scenes_template import ScenesTemplate


class BaseScenesTemplateRepository(ABC):
    """Where the scenes templates are kept."""

    @abstractmethod
    async def list_all(self) -> list[ScenesTemplate]:
        """Return every scenes template."""

    @abstractmethod
    async def get(self, *, template_id: str) -> ScenesTemplate | None:
        """Return one scenes template, or nothing when there is none."""
