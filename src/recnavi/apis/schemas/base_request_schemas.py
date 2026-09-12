# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.

"""api request schemas."""

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import alias_generators


class BaseItemModel(BaseModel):
    """Base item model."""

    model_config = ConfigDict(
        alias_generator=alias_generators.to_camel,
        populate_by_name=True,
    )
