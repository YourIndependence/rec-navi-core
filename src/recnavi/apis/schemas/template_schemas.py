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
from pydantic import field_validator

from recnavi.apis.schemas.base_response_schemas import BaseApiResponseModel
from recnavi.core.types.scenes_template import ScenesTemplate


class GetTemplatesResponse(BaseModel):
    """Response for GET /getTemplates."""

    model_config = ConfigDict(
        alias_generator=alias_generators.to_camel,
        populate_by_name=True,
    )
    status: str = Field(default="ok", description="Response status")

    templates: list[ScenesTemplate] = Field(
        ...,
        description="List of all scenes templates",
    )


class UpdateTemplateRequest(ScenesTemplate):
    """Create or update the template identified by a required client key."""

    title: str | None = Field(default=None, min_length=1)
    scene_principals: list[str] | None = None
    thumbnail_image: str | None = None

    @field_validator("thumbnail_image")
    @classmethod
    def validate_image(cls, value: str | None) -> str | None:
        """Apply the domain image rule to transport input."""
        return ScenesTemplate.validate_image(value)


class UpdateTemplateResponse(BaseApiResponseModel):
    """Response for POST /updateTemplate."""

    template: ScenesTemplate = Field(..., description="Updated template")
