# Copyright (c) 2025 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.


"""api response schemas."""

from enum import Enum

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field
from pydantic import alias_generators

from recnavi.core.types.x_user import XUser
from recnavi.core.types.project_item import ProjectItem


class ResponseStatus(str, Enum):
    """Response status enumeration."""

    OK = "ok"
    ERROR = "error"


class BaseApiResponseModel(BaseModel):
    """Base API response model."""

    model_config = ConfigDict(
        alias_generator=alias_generators.to_camel,
        populate_by_name=True,
    )

    status: ResponseStatus = Field(
        default=ResponseStatus.OK, description="Response status"
    )
    message: str | None = Field(default=None, description="Optional message")


class GreetingResponse(BaseApiResponseModel):
    """Greeting API response model."""

    x_user: XUser


class ProjectsListResponse(BaseApiResponseModel):
    projects: list(ProjectItem)
