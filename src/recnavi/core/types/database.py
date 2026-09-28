# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.

"""database type"""

from typing import Any

from pydantic import BaseModel
from pydantic import Field


class DatabaseQueryResult(BaseModel):
    """Result from database query or scan operations with pagination support.

    Attributes:
        items: List of items returned from the query/scan.
        last_evaluated_key: Key to continue pagination, or None if no more items.

    """

    items: list[dict[str, Any]] = Field(
        ...,
        description="Items returned from the database operation",
    )
    last_evaluated_key: dict[str, Any] | None = Field(
        default=None,
        description="Pagination key for next page, None if last page",
    )
