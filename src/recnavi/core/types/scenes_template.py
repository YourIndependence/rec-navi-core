# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.


"""ScenesTemplate"""

from typing import Self

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field
from pydantic import alias_generators

from recnavi.core.storage.base_object_storage import BaseObjectStorage
from recnavi.core.storage.image_urls import generate_image_url


class ScenesTemplate(BaseModel):
    """A named set of scene masters an owner can start a project from."""

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
    thumbnail_uri: str | None = Field(
        default=None,
        exclude=True,
        description="Location of the image shown on the template tile",
    )
    thumbnail_url: str | None = Field(
        default=None,
        description="Presigned URL of the template thumbnail",
    )

    async def attach_presigned_url(
        self,
        *,
        storage: BaseObjectStorage,
    ) -> Self:
        """Refresh the thumbnail URL on this template and return self."""
        self.thumbnail_url = await generate_image_url(
            storage=storage,
            image_uri=self.thumbnail_uri,
        )
        return self

    def to_storage_item(self) -> dict[str, object]:
        """Serialize durable references without temporary image URLs."""
        return {
            **self.model_dump(by_alias=True, exclude={"thumbnail_url"}),
            "thumbnailUri": self.thumbnail_uri,
        }
