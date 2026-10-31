# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.


"""ScenesTemplate"""

import base64
import binascii
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
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


class ScenesTemplate(BaseModel):
    """A named set of scene masters an owner can start a project from."""

    model_config = ConfigDict(
        alias_generator=alias_generators.to_camel,
        populate_by_name=True,
        validate_assignment=True,
    )

    template_id: str = Field(
        ...,
        pattern=r"^[A-Za-z0-9][A-Za-z0-9_-]{0,127}$",
        description="Identifier of the scenes template",
    )
    title: str = Field(
        ...,
        min_length=1,
        description="Name shown to the account owner",
    )
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

    @staticmethod
    def validate_image(value: str | None) -> str | None:
        """Validate raw base64 before touching storage."""
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
    async def update_thumbnail(
        self,
        *,
        storage: BaseObjectStorage,
        thumbnail_image: str,
    ) -> AsyncIterator[Self]:
        """Publish a replacement only when its database write succeeds."""
        self.validate_image(thumbnail_image)
        previous_uri = self.thumbnail_uri
        previous_url = self.thumbnail_url
        object_key = (
            f"templates/{self.template_id}/{uuid4().hex}/thumbnail.jpg"
        )
        committed = False
        try:
            await storage.upload_base64(
                object_key=object_key,
                base64_data=thumbnail_image,
                content_type="image/jpeg",
            )
            self.thumbnail_uri = object_key
            self.thumbnail_url = None
            yield self
            committed = True
        finally:
            if not committed:
                self.thumbnail_uri = previous_uri
                self.thumbnail_url = previous_url
                await storage.delete_object_by_key(object_key=object_key)
        if previous_uri is not None:
            await storage.delete_object_by_key(
                object_key=previous_uri.removeprefix(
                    f"s3://{MEDIA_BUCKET_NAME}/",
                ),
            )

    async def save(self, *, templates_db: BaseDatabase) -> Self:
        """Persist durable references and return this template."""
        await templates_db.put_item(self.to_storage_item())
        return self
