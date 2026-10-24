# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.

"""Tests for CloudWatch custom metrics."""

from unittest.mock import AsyncMock
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest

from recnavi.core.project.projects import build_filter_stats
from recnavi.infrastructure.cloudwatch import cloudwatch_metrics
from recnavi.infrastructure.cloudwatch.cloudwatch_metrics import (
    CloudWatchMetricsPublisher,
)


MODULE = "recnavi.infrastructure.cloudwatch.cloudwatch_metrics"


def _session_with(cloudwatch: AsyncMock) -> MagicMock:
    client_cm = MagicMock()
    client_cm.__aenter__ = AsyncMock(return_value=cloudwatch)
    client_cm.__aexit__ = AsyncMock(return_value=None)
    session = MagicMock()
    session.client.return_value = client_cm
    return session


def test_build_metric_data_has_the_three_metrics():
    """Test the metric names and values follow the issue definition."""
    stats = build_filter_stats(queried_count=100, filtered_count=5)

    data = cloudwatch_metrics.build_metric_data(stats)

    assert {d["MetricName"]: d["Value"] for d in data} == {
        "GetMyProjects.QueriedCount": 100,
        "GetMyProjects.FilteredCount": 5,
        "GetMyProjects.FilterRatio": 95.0,
    }


@pytest.mark.asyncio
async def test_publish_project_filter_stats_is_noop_in_local_environments():
    """Test nothing is published from LOCAL or CI."""
    stats = build_filter_stats(queried_count=10, filtered_count=1)

    with (
        patch(f"{MODULE}.ENV", "CI"),
        patch(f"{MODULE}.aioboto3.Session") as session_cls,
    ):
        await CloudWatchMetricsPublisher().publish_project_filter_stats(stats)

    session_cls.assert_not_called()


@pytest.mark.asyncio
async def test_publish_project_filter_stats_publishes_in_deployed_environments():
    """Test metrics are published to CloudWatch outside LOCAL and CI."""
    cloudwatch = AsyncMock()
    stats = build_filter_stats(queried_count=10, filtered_count=1)

    with (
        patch(f"{MODULE}.ENV", "dev"),
        patch(
            f"{MODULE}.aioboto3.Session",
            return_value=_session_with(cloudwatch),
        ),
    ):
        await CloudWatchMetricsPublisher().publish_project_filter_stats(stats)

    cloudwatch.put_metric_data.assert_awaited_once()
    kwargs = cloudwatch.put_metric_data.await_args.kwargs
    assert kwargs["Namespace"] == "RecNavi"
    assert len(kwargs["MetricData"]) == 3


@pytest.mark.asyncio
async def test_transport_failure_is_logged_without_failing_listing(caplog):
    from botocore.exceptions import EndpointConnectionError

    cloudwatch = AsyncMock()
    cloudwatch.put_metric_data.side_effect = EndpointConnectionError(
        endpoint_url="https://cloudwatch.invalid",
    )
    stats = build_filter_stats(queried_count=10, filtered_count=1)
    with (
        patch(f"{MODULE}.ENV", "dev"),
        patch(
            f"{MODULE}.aioboto3.Session",
            return_value=_session_with(cloudwatch),
        ),
    ):
        await CloudWatchMetricsPublisher().publish_project_filter_stats(stats)
    assert "failed to put getMyProjects metrics" in caplog.text
