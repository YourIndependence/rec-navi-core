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
from collections.abc import AsyncIterator
from collections.abc import Sequence
from contextlib import asynccontextmanager
from typing import Self
from uuid import uuid4

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field
from pydantic import alias_generators

from recnavi.config.variables import MEDIA_BUCKET_NAME
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

    @asynccontextmanager
    async def update_images(
        self,
        *,
        storage: BaseObjectStorage,
        example_image: str | None,
        guide_image: str | None,
    ) -> AsyncIterator[Self]:
        """Stage images and finalize them when the caller's persistence succeeds."""
        example_image = self.validate_image(example_image)
        guide_image = self.validate_image(guide_image)
        if example_image is None and guide_image is None:
            raise ClientValueError("At least one image must be provided")

        image_prefix = f"scenes/{self.scene_principal}/{uuid4().hex}/"
        previous_images = (self.thumbnail_uri, self.guide_uri)
        committed = False
        try:
            await self._upload_images(
                storage=storage,
                image_prefix=image_prefix,
                example_image=example_image,
                guide_image=guide_image,
            )
            yield self
            committed = True
        finally:
            if committed:
                await self._delete_replaced_images(
                    storage=storage,
                    previous_images=previous_images,
                )
            else:
                try:
                    await storage.delete_objects_by_prefix(prefix=image_prefix)
                finally:
                    self.thumbnail_uri, self.guide_uri = previous_images

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

    async def _upload_images(
        self,
        *,
        storage: BaseObjectStorage,
        image_prefix: str,
        example_image: str | None,
        guide_image: str | None,
    ) -> None:
        if example_image is not None:
            self.thumbnail_uri = await self._upload_image(
                storage=storage,
                object_key=f"{image_prefix}example.jpg",
                image=example_image,
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

    async def _delete_replaced_images(
        self,
        *,
        storage: BaseObjectStorage,
        previous_images: Sequence[str | None],
    ) -> None:
        current_images = {self.thumbnail_uri, self.guide_uri}
        owned_prefix = f"scenes/{self.scene_principal}/"
        for image_uri in set(previous_images) - current_images:
            if image_uri is None:
                continue
            object_key = image_uri.removeprefix(f"s3://{MEDIA_BUCKET_NAME}/")
            if object_key.startswith(owned_prefix):
                await storage.delete_object_by_key(object_key=object_key)
