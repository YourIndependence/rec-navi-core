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

from recnavi.core.types.scenes_template import ScenesTemplate


class GetTemplatesResponse(BaseModel):
    """Response for GET /getTemplates."""

    model_config = ConfigDict(
        alias_generator=alias_generators.to_camel,
        populate_by_name=True,
    )

    status: str = Field(default="ok", description="Response status")
    templates: list[ScenesTemplate]


class UpdateTemplateRequest(BaseModel):
    """Request for POST /updateTemplate (admin-only)."""

    model_config = ConfigDict(
        alias_generator=alias_generators.to_camel,
        populate_by_name=True,
    )

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


class UpdateTemplateResponse(BaseModel):
    """Response for POST /updateTemplate."""

    model_config = ConfigDict(
        alias_generator=alias_generators.to_camel,
        populate_by_name=True,
    )

    status: str = Field(default="ok", description="Response status")
    templates: list[ScenesTemplate] = Field(..., description="All templates")
