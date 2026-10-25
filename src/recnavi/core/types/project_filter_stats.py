# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.

"""Statistics of one filtered project listing page."""

from pydantic import BaseModel
from pydantic import Field


class ProjectFilterStats(BaseModel):
    """How many rows one page read and how many survived the filter."""

    queried_count: int = Field(..., description="Rows read from the database")
    filtered_count: int = Field(..., description="Rows returned to the caller")
    filter_ratio: float = Field(
        ...,
        description="Percentage of queried rows dropped by the filter",
    )
