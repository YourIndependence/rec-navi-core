# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.

"""Validated scene master write data."""

import base64
import binascii

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field
from pydantic import alias_generators
from pydantic import field_validator


class SceneMasterUpdate(BaseModel):
    """Editable master metadata and optional replacement images."""

    model_config = ConfigDict(
        alias_generator=alias_generators.to_camel,
        populate_by_name=True,
    )

    scene_principal: str = Field(
        ...,
        pattern=r"^[A-Za-z0-9][A-Za-z0-9_-]{0,127}$",
        description="Human-readable master key supplied by the client",
    )
    title: str = Field(..., min_length=1)
    max_duration_seconds: int = Field(..., ge=1, le=10)
    example_image: str | None = None
    guide_image: str | None = None

    @field_validator("example_image", "guide_image")
    @classmethod
    def validate_image(cls, value: str | None) -> str | None:
        """Reject malformed or empty image payloads before storage I/O."""
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


class SceneMasterCreate(SceneMasterUpdate):
    """A new master requires both example and framing guide images."""

    example_image: str
    guide_image: str
