# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.


"""SceneMaster"""

import base64
import binascii
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
        pattern=r"^[A-Za-z0-9][A-Za-z0-9_-]{0,127}$",
        description="Human-readable master key supplied by the client",
    )
    title: str = Field(
        ...,
        min_length=1,
        description="Name shown to the staff",
    )
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
        ge=1,
        le=10,
        description="How long the staff may record",
    )

    thumbnail_url: str | None = None
    guide_url: str | None = None

    @staticmethod
    def validate_image(value: str | None) -> str | None:
        """Validate optional image data before any uploads."""
        if value is not None:
            try:
                decoded = base64.b64decode(value, validate=True)
            except (ValueError, binascii.Error) as error:
                raise ValueError(
                    "Image must contain valid base64 data",
                ) from error
            if not decoded:
                raise ValueError("Image must not be empty")
        return value

    async def upload_images(
        self,
        *,
        storage: BaseObjectStorage,
        bucket_name: str,
        image_prefix: str,
        example_image: str | None,
        guide_image: str | None,
    ) -> Self:
        """Replace provided images, preserve omitted images, and return self."""
        example_image = self.validate_image(example_image)
        guide_image = self.validate_image(guide_image)
        if example_image is not None:
            object_key = f"{image_prefix}example.jpg"
            await storage.upload_base64(
                object_key=object_key,
                base64_data=example_image,
                content_type="image/jpeg",
            )
            self.thumbnail_uri = f"s3://{bucket_name}/{object_key}"
        if guide_image is not None:
            object_key = f"{image_prefix}guide.jpg"
            await storage.upload_base64(
                object_key=object_key,
                base64_data=guide_image,
                content_type="image/jpeg",
            )
            self.guide_uri = f"s3://{bucket_name}/{object_key}"
        return self

    async def attach_presigned_url(
        self,
        *,
        storage: BaseObjectStorage,
    ) -> Self:
        """Refresh image URLs on this master and return self."""
        self.thumbnail_url = await generate_image_url(
            storage=storage,
            image_uri=self.thumbnail_uri,
        )
        self.guide_url = await generate_image_url(
            storage=storage,
            image_uri=self.guide_uri,
        )
        return self

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
