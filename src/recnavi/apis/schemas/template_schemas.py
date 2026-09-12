# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.

"""Template-related API schemas."""

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field
from pydantic import alias_generators


class TemplateView(BaseModel):
    """Template view for API responses.

    This schema excludes S3 object key (thumbnailUri) from the response.
    Clients request images via separate endpoints using templateId.
    """

    model_config = ConfigDict(
        alias_generator=alias_generators.to_camel,
        populate_by_name=True,
    )

    template_id: str = Field(
        ...,
        description="Identifier of the scenes template",
    )
    title: str = Field(..., description="Name shown to the account owner")
    scene_principals: list[str] = Field(
        default_factory=list,
        description="Scene masters to lay out, in shooting order",
    )


class GetTemplatesResponse(BaseModel):
    """Response for GET /getTemplates."""

    model_config = ConfigDict(
        alias_generator=alias_generators.to_camel,
        populate_by_name=True,
    )

    status: str = Field(default="ok", description="Response status")
    templates: list[TemplateView] = Field(
        ...,
        description="List of all scenes templates",
    )
