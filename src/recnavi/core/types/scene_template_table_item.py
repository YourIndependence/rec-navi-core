# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.

"""SceneTemplateTableItem"""

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field
from pydantic import alias_generators


class SceneTemplateTableItem(BaseModel):
    """sceneTemplates table item. Named bundle of scene definitions."""

    model_config = ConfigDict(
        alias_generator=alias_generators.to_camel,
        populate_by_name=True,
    )

    template_id: str = Field(..., description="partition key")
    title: str = Field(..., description="display title")
    scene_principals: list[str] = Field(
        default_factory=list,
        description="ordered scenes table keys",
    )
    thumbnail_uri: str = Field(
        ...,
        description="S3 object key of the tile image",
    )
