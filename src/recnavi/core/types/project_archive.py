# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.

"""Project archive"""

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field
from pydantic import alias_generators


class ProjectArchive(BaseModel):
    """A downloadable zip archive of a project."""

    model_config = ConfigDict(
        alias_generator=alias_generators.to_camel,
        populate_by_name=True,
    )

    download_url: str = Field(
        ...,
        description="Presigned URL to download the zip archive",
    )
    expires_in_seconds: int = Field(
        ...,
        description="Seconds until the download URL expires",
    )
