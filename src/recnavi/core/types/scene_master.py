# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.


"""SceneMaster"""

from typing import Self

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field
from pydantic import alias_generators

from recnavi.core.storage.base_object_storage import BaseObjectStorage
from recnavi.core.storage.image_urls import generate_image_url


class SceneMaster(BaseModel):
    """How a kind of scene is meant to be shot."""

    model_config = ConfigDict(
        alias_generator=alias_generators.to_camel,
        populate_by_name=True,
    )

    scene_principal: str = Field(
        ...,
        description="Identifier of the scene master",
    )
    title: str = Field(..., description="Name shown to the staff")
    thumbnail_uri: str | None = Field(
        default=None,
        exclude=True,
        description="Location of the example photo to imitate",
    )
    guide_uri: str | None = Field(
        default=None,
        exclude=True,
        description="Location of the framing guide laid over the camera",
    )
    max_duration_seconds: int = Field(
        ...,
        description="How long the staff may record",
    )

    thumbnail_url: str | None = None
    guide_url: str | None = None

    async def attach_presigned_url(
        self,
        *,
        storage: BaseObjectStorage,
    ) -> Self:
        """Return a copy with fresh image URLs and unchanged storage references."""
        return self.model_copy(
            update={
                "thumbnail_url": await generate_image_url(
                    storage=storage,
                    image_uri=self.thumbnail_uri,
                ),
                "guide_url": await generate_image_url(
                    storage=storage,
                    image_uri=self.guide_uri,
                ),
            },
            deep=True,
        )

    def to_storage_item(self) -> dict[str, object]:
        """Serialize durable references without temporary image URLs."""
        return {
            **self.model_dump(
                by_alias=True,
                exclude={"thumbnail_url", "guide_url"},
            ),
            "thumbnailUri": self.thumbnail_uri,
            "guideUri": self.guide_uri,
        }
