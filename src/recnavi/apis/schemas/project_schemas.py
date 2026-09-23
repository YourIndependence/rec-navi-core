# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.

"""Project API schemas."""

from pydantic import BaseModel
from pydantic import Field


class DownloadProjectRequest(BaseModel):
    """Request schema for POST /downloadProject."""

    project_id: str = Field(
        ...,
        alias="projectId",
        description="Project identifier",
    )


class DownloadProjectResponse(BaseModel):
    """Response schema for POST /downloadProject."""

    status: str = Field(
        default="ok",
        description="Response status (always 'ok' on success)",
    )
    download_url: str = Field(
        ...,
        alias="downloadUrl",
        description="Presigned S3 URL for zip archive download (1-hour expiration)",
    )
