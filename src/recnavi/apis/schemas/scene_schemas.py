# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.

"""Scene-related API schemas."""

from typing import TYPE_CHECKING

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field
from pydantic import alias_generators


if TYPE_CHECKING:
    from recnavi.core.types.project import Project


class SceneMasterView(BaseModel):
    """Scene master view for API responses.

    This schema excludes S3 object keys (thumbnailUri, guideUri) from the
    response. Clients request these via separate endpoints using scenePrincipal.
    """

    model_config = ConfigDict(
        alias_generator=alias_generators.to_camel,
        populate_by_name=True,
    )

    scene_principal: str = Field(
        ...,
        description="Identifier of the scene master",
    )
    title: str = Field(..., description="Name shown to the staff")
    max_duration_seconds: int = Field(
        ...,
        description="How long the staff may record",
    )


class GetSceneMastersResponse(BaseModel):
    """Response for GET /getSceneMasters."""

    model_config = ConfigDict(
        alias_generator=alias_generators.to_camel,
        populate_by_name=True,
    )

    status: str = Field(default="ok", description="Response status")
    scenes: list[SceneMasterView] = Field(
        ...,
        description="List of all scene masters",
    )


class UpdateSceneRecordRequest(BaseModel):
    """Request for POST /updateSceneRecord."""

    model_config = ConfigDict(
        alias_generator=alias_generators.to_camel,
        populate_by_name=True,
    )

    project_id: str = Field(..., description="Project ID")
    scene_id: str = Field(..., description="Scene ID")
    video: str = Field(..., description="Base64-encoded video data")
    thumbnail: str = Field(..., description="Base64-encoded thumbnail data")


class UpdateSceneRecordResponse(BaseModel):
    """Response for POST /updateSceneRecord."""

    model_config = ConfigDict(
        alias_generator=alias_generators.to_camel,
        populate_by_name=True,
        from_attributes=True,
    )

    status: str = Field(default="ok", description="Response status")
    project: "Project"  # Forward reference


class ReviewSceneRequest(BaseModel):
    """Request for POST /reviewScene."""

    model_config = ConfigDict(
        alias_generator=alias_generators.to_camel,
        populate_by_name=True,
    )

    project_id: str = Field(..., description="Project ID")
    scene_id: str = Field(..., description="Scene ID")
    result: str = Field(..., description="Review result (approve or reject)")
    comment: str | None = Field(default=None, description="Review comment")


class ReviewSceneResponse(BaseModel):
    """Response for POST /reviewScene."""

    model_config = ConfigDict(
        alias_generator=alias_generators.to_camel,
        populate_by_name=True,
        from_attributes=True,
    )

    status: str = Field(default="ok", description="Response status")
    project: "Project"  # Forward reference
