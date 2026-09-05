# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.


"""ImageAsset"""

import mimetypes

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field
from pydantic import alias_generators


FALLBACK_MEDIA_TYPE = "application/octet-stream"


class ImageAsset(BaseModel):
    """An image served as the body of a response."""

    model_config = ConfigDict(
        alias_generator=alias_generators.to_camel,
        populate_by_name=True,
    )

    content: bytes = Field(..., description="The image itself")
    media_type: str = Field(..., description="What the bytes are")

    @classmethod
    def of(cls, *, content: bytes, uri: str) -> "ImageAsset":
        """Build an image, naming the bytes after the stored object."""
        return cls(content=content, media_type=media_type_of(uri))


def media_type_of(uri: str) -> str:
    """Name the bytes after the extension the object was stored under.

    The ContentType S3 reports depends on how the object was uploaded and
    is often binary/octet-stream. The extension is what we control.
    """
    guessed, _ = mimetypes.guess_type(uri)
    return guessed or FALLBACK_MEDIA_TYPE
