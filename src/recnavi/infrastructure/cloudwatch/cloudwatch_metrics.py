# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.

"""CloudWatch custom metrics for project listing."""

import logging

import aioboto3
from botocore.exceptions import BotoCoreError
from botocore.exceptions import ClientError

from recnavi.config.variables import ENV
from recnavi.config.variables import REGION
from recnavi.core.metrics.base_metrics_publisher import BaseMetricsPublisher
from recnavi.core.types.project_filter_stats import ProjectFilterStats


logger = logging.getLogger(__name__)

METRIC_NAMESPACE = "RecNavi"
LOCAL_ENVIRONMENTS = ("LOCAL", "CI")


def build_metric_data(stats: ProjectFilterStats) -> list[dict[str, object]]:
    """Build the CloudWatch metric data for one listing page."""
    dimensions = [{"Name": "Environment", "Value": ENV}]
    return [
        {
            "MetricName": "GetMyProjects.QueriedCount",
            "Dimensions": dimensions,
            "Value": stats.queried_count,
            "Unit": "Count",
        },
        {
            "MetricName": "GetMyProjects.FilteredCount",
            "Dimensions": dimensions,
            "Value": stats.filtered_count,
            "Unit": "Count",
        },
        {
            "MetricName": "GetMyProjects.FilterRatio",
            "Dimensions": dimensions,
            "Value": stats.filter_ratio,
            "Unit": "Percent",
        },
    ]


class CloudWatchMetricsPublisher(BaseMetricsPublisher):
    """Publish metrics as CloudWatch custom metrics."""

    async def publish_project_filter_stats(
        self,
        stats: ProjectFilterStats,
    ) -> None:
        """Record filter statistics as CloudWatch custom metrics.

        Does nothing outside deployed environments. A failure to publish is
        logged and never fails the request.
        """
        if ENV in LOCAL_ENVIRONMENTS:
            return

        session = aioboto3.Session()
        try:
            async with session.client("cloudwatch", region_name=REGION) as cw:
                await cw.put_metric_data(
                    Namespace=METRIC_NAMESPACE,
                    MetricData=build_metric_data(stats),
                )
        except (ClientError, BotoCoreError):
            logger.warning(
                "failed to put getMyProjects metrics",
                exc_info=True,
            )
