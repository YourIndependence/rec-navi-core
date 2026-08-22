# Copyright (c) 2025 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.

# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.


"""SceneTableItem"""

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field
from pydantic import alias_generators


class SceneTableItem(BaseModel):
    """scenes table item. Scene definition master."""

    model_config = ConfigDict(
        alias_generator=alias_generators.to_camel,
        populate_by_name=True,
    )

    scene_principal: str = Field(..., description="partition key")
    title: str = Field(..., description="display title")
    thumbnail_uri: str = Field(
        ...,
        description="S3 object key of the example photo",
    )
    guide_uri: str = Field(
        ...,
        description="S3 object key of the transparent PNG guide",
    )
    max_duration_seconds: int = Field(
        ...,
        description="max recording duration in seconds",
    )
