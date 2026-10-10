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


class GetSceneMastersResponse(BaseApiResponseModel):
    """Response for GET /getSceneMasters."""

    scenes: list[SceneMasterView] = Field(
        ...,
        description="List of all scene masters",
    )


class SceneMasterInput(BaseItemModel):
    """Scene master fields sent by the client (mirrors SceneMaster).

    URIs are excluded; images are sent separately on the request.
    """

    scene_principal: str | None = Field(
        None,
        description="Identifier of the scene master (null creates a new one)",
    )
    title: str = Field(..., description="Name shown to the staff")
    max_duration_seconds: int = Field(
        ...,
        description="How long the staff may record (1-10 seconds)",
    )


class UpdateSceneRequest(BaseItemModel):
    """Request for POST /updateScene (admin-only).

    Creates a new scene master when scene.scenePrincipal is null,
    otherwise upserts the scene master with the given scenePrincipal.
    """

    scene: SceneMasterInput = Field(..., description="Scene master to save")
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


class UpdateSceneResponse(BaseApiResponseModel):
    """Response for POST /updateScene."""

    scenes: list[SceneMasterView] = Field(
        ...,
        description="List of all scene masters after update",
    )
