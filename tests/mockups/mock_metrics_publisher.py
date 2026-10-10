# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.

"""Mock metrics publisher for testing."""

from recnavi.core.metrics.base_metrics_publisher import BaseMetricsPublisher
from recnavi.core.types.project_filter_stats import ProjectFilterStats


class MockMetricsPublisher(BaseMetricsPublisher):
    """In-memory publisher that records the published statistics."""

    def __init__(self) -> None:
        """Initialize with nothing published."""
        self.published: list[ProjectFilterStats] = []

    async def publish_project_filter_stats(
        self,
        stats: ProjectFilterStats,
    ) -> None:
        """Record the statistics."""
        self.published.append(stats)
