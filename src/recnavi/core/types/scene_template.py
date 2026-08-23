# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.


"""SceneTemplate"""

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field
from pydantic import alias_generators


class SceneTemplate(BaseModel):
    """A named set of scene masters an owner can start a project from."""

    model_config = ConfigDict(
        alias_generator=alias_generators.to_camel,
        populate_by_name=True,
    )

    template_id: str = Field(
        ...,
        description="Identifier of the scene template",
    )
    title: str = Field(..., description="Name shown to the account owner")
    scene_principals: list[str] = Field(
        default_factory=list,
        description="Scene masters to lay out, in shooting order",
    )
    thumbnail_uri: str = Field(
        ...,
        description="Location of the image shown on the template tile",
    )
