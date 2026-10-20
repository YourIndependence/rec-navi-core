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
from uuid import uuid4

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field
from pydantic import alias_generators

from recnavi.config.variables import MEDIA_BUCKET_NAME
from recnavi.core.database.base_database import BaseDatabase
from recnavi.core.storage.base_object_storage import BaseObjectStorage
from recnavi.core.storage.image_urls import generate_image_url
from recnavi.exceptions.exceptions import ClientValueError


class SceneMaster(BaseModel):
    """How a kind of scene is meant to be shot."""

    model_config = ConfigDict(
        alias_generator=alias_generators.to_camel,
        populate_by_name=True,
        validate_assignment=True,
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
        description="Location of the scene master thumbnail",
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

    async def update_images(
        self,
        *,
        storage: BaseObjectStorage,
        thumbnail_image: str | None,
        guide_image: str | None,
    ) -> Self:
        """Upload replacements, delete previous images, and return this master."""
        if thumbnail_image is None and guide_image is None:
            raise ClientValueError("At least one image must be provided")

        if thumbnail_image is None:
            previous_thumbnail_uri = None
        else:
            previous_thumbnail_uri = self.thumbnail_uri

        if guide_image is None:
            previous_guide_uri = None
        else:
            previous_guide_uri = self.guide_uri

        thumbnail_image = self.validate_image(thumbnail_image)
        guide_image = self.validate_image(guide_image)
        image_prefix = f"scenes/{self.scene_principal}/{uuid4().hex}/"

        await self._upload_images(
            storage=storage,
            image_prefix=image_prefix,
            thumbnail_image=thumbnail_image,
            guide_image=guide_image,
        )
        for previous_image_uri in (previous_thumbnail_uri, previous_guide_uri):
            if previous_image_uri is None:
                continue
            object_key = previous_image_uri.removeprefix(
                f"s3://{MEDIA_BUCKET_NAME}/",
            )
            await storage.delete_object_by_key(object_key=object_key)
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

    async def save(self, *, scenes_db: BaseDatabase) -> Self:
        """Persist durable references and return this master."""
        await scenes_db.put_item(self.to_storage_item())
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

    async def _upload_images(
        self,
        *,
        storage: BaseObjectStorage,
        image_prefix: str,
        thumbnail_image: str | None,
        guide_image: str | None,
    ) -> None:
        if thumbnail_image is not None:
            self.thumbnail_uri = await self._upload_image(
                storage=storage,
                object_key=f"{image_prefix}thumbnail.jpg",
                image=thumbnail_image,
            )
        if guide_image is not None:
            self.guide_uri = await self._upload_image(
                storage=storage,
                object_key=f"{image_prefix}guide.jpg",
                image=guide_image,
            )

    @staticmethod
    async def _upload_image(
        *,
        storage: BaseObjectStorage,
        object_key: str,
        image: str,
    ) -> str:
        await storage.upload_base64(
            object_key=object_key,
            base64_data=image,
            content_type="image/jpeg",
        )
        return object_key
