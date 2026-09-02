# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.


"""master api schemas."""

from collections.abc import Sequence

from pydantic import Field

from recnavi.apis.schemas.request_schemas import BaseItemModel
from recnavi.apis.schemas.response_schemas import BaseApiResponseModel
from recnavi.core.types.scene_master import SceneMaster


class SceneMasterView(BaseItemModel):
    """A scene master as the client sees it.

    The object keys are left out on purpose. The client asks for the
    images by principal, so where they are stored stays on the server.
    """

    scene_principal: str = Field(
        ...,
        description="Identifier of the scene master",
    )
    title: str = Field(..., description="Name shown to the staff")
    max_duration_seconds: int = Field(
        ...,
        description="How long the staff may record",
    )

    @classmethod
    def from_scene_master(cls, master: SceneMaster) -> "SceneMasterView":
        """Show only what the client is meant to see."""
        return cls(
            scene_principal=master.scene_principal,
            title=master.title,
            max_duration_seconds=master.max_duration_seconds,
        )


class GetSceneMastersResponse(BaseApiResponseModel):
    """getSceneMasters API response model."""

    scenes: list[SceneMasterView] = Field(
        default_factory=list,
        description="Every scene master",
    )

    @classmethod
    def from_scene_masters(
        cls,
        masters: Sequence[SceneMaster],
    ) -> "GetSceneMastersResponse":
        """Build the response from the domain objects."""
        return cls(
            scenes=[
                SceneMasterView.from_scene_master(master) for master in masters
            ],
        )
