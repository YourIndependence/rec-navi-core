# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.

"""Scene-related API schemas."""

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field
from pydantic import alias_generators

from recnavi.apis.schemas.base_request_schemas import BaseItemModel
from recnavi.apis.schemas.base_response_schemas import BaseApiResponseModel
from recnavi.core.types.project import Project
from recnavi.core.types.scene import ReviewSceneResult
from recnavi.core.types.scene_master import SceneMaster


class GetSceneMastersResponse(BaseModel):
    """Response for GET /getSceneMasters."""

    model_config = ConfigDict(
        alias_generator=alias_generators.to_camel,
        populate_by_name=True,
    )

    status: str = Field(default="ok", description="Response status")
    scenes: list[SceneMaster] = Field(
        ...,
        description="List of all scene masters",
    )


class ReviewSceneRequest(BaseItemModel):
    """Request for POST /reviewScene."""

    project_id: str = Field(..., description="Project ID")
    scene_id: str = Field(..., description="Scene ID")
    result: ReviewSceneResult = Field(..., description="Review result")
    comment: str | None = Field(default=None, description="Review comment")


class ReviewSceneResponse(BaseApiResponseModel):
    """Response for POST /reviewScene."""

    model_config = ConfigDict(from_attributes=True)

    project: Project = Field(..., description="Updated project")


class UpdateSceneRequest(BaseItemModel):
    """Request for POST /updateScene."""

    project_id: str = Field(..., description="Project ID")
    scene_id: str = Field(..., description="Scene ID")
    video: str = Field(..., description="Base64-encoded video data")
    thumbnail: str = Field(..., description="Base64-encoded thumbnail data")


class UpdateSceneResponse(BaseApiResponseModel):
    """Response for POST /updateScene."""

    model_config = ConfigDict(from_attributes=True)

    project: Project = Field(..., description="Updated project")


class UpdateSceneMasterRequest(BaseItemModel):
    """Request for POST /updateSceneMaster.

    Creates a new scene master when scenePrincipal is null,
    otherwise upserts the scene master with the given scenePrincipal.
    """

    scene_principal: str | None = Field(
        None,
        description="Identifier of the scene master (null creates a new one)",
    )
    title: str = Field(..., description="Name shown to the staff")
    max_duration_seconds: int = Field(
        ...,
        ge=1,
        le=10,
        description="How long the staff may record (1-10 seconds)",
    )

    example_image: str | None = Field(
        None,
        description=(
            "Base64-encoded example photo "
            "(required on create, optional on update)"
        ),
    )
    guide_image: str | None = Field(
        None,
        description=(
            "Base64-encoded framing guide "
            "(required on create, optional on update)"
        ),
    )


class UpdateSceneMasterResponse(BaseApiResponseModel):
    """Response for POST /updateSceneMaster."""

    scene_master: SceneMaster = Field(
        ...,
        description="Updated scene master with temporary image URLs",
    )
