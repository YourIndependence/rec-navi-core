# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.

"""Metrics publisher abstraction."""

from abc import ABC
from abc import abstractmethod

from recnavi.core.types.project_filter_stats import ProjectFilterStats


class BaseMetricsPublisher(ABC):
    """Abstract publisher that sends operational metrics to a backend."""

    @abstractmethod
    async def publish_project_filter_stats(
        self,
        stats: ProjectFilterStats,
    ) -> None:
        """Publish the filter statistics of one project listing page.

        Args:
            stats: Filter statistics of the page.

        """
        pass
