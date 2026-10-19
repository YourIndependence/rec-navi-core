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

from recnavi.core.types.scenes_template import ScenesTemplateView


class GetTemplatesResponse(BaseModel):
    """Response for GET /getTemplates."""

    model_config = ConfigDict(
        alias_generator=alias_generators.to_camel,
        populate_by_name=True,
    )

    status: str = Field(default="ok", description="Response status")
    templates: list[ScenesTemplateView] = Field(
        ...,
        description="List of all scenes templates",
    )
