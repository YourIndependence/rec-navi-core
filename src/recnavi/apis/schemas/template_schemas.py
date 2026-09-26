# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.

"""Template-related API schemas."""

from pydantic import Field

from recnavi.apis.schemas.base_request_schemas import BaseItemModel
from recnavi.apis.schemas.base_response_schemas import BaseApiResponseModel
from recnavi.core.types.scenes_template import ScenesTemplate


class GetTemplatesResponse(BaseApiResponseModel):
    """Response for GET /getTemplates."""

    templates: list[ScenesTemplate] = Field(
        ...,
        description="List of all scenes templates",
    )


class UpdateTemplateRequest(BaseItemModel):
    """Request for POST /updateTemplate (admin-only)."""

    template_id: str = Field(..., description="Identifier of the template")
    title: str = Field(..., description="Name shown to the owner")
    scene_principals: list[str] = Field(
        ...,
        description="Scene masters to lay out, in shooting order",
    )
    thumbnail: str | None = Field(
        None,
        description="Base64-encoded JPEG (required on create, optional on update)",
    )


class UpdateTemplateResponse(BaseApiResponseModel):
    """Response for POST /updateTemplate."""

    templates: list[ScenesTemplate] = Field(..., description="All templates")
