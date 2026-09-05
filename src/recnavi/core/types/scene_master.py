# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.


"""SceneMaster"""

from enum import StrEnum

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field
from pydantic import alias_generators


class SceneImageKind(StrEnum):
    """Which of a scene master's two images is wanted."""

    EXAMPLE = "example"
    GUIDE = "guide"


class SceneMaster(BaseModel):
    """How a kind of scene is meant to be shot."""

    model_config = ConfigDict(
        alias_generator=alias_generators.to_camel,
        populate_by_name=True,
    )

    scene_principal: str = Field(
        ...,
        description="Identifier of the scene master",
    )
    title: str = Field(..., description="Name shown to the staff")
    thumbnail_uri: str = Field(
        ...,
        description="Location of the example photo to imitate",
    )
    guide_uri: str = Field(
        ...,
        description="Location of the framing guide laid over the camera",
    )
    max_duration_seconds: int = Field(
        ...,
        description="How long the staff may record",
    )
