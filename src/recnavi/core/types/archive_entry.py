# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.

"""Object-storage archive entry descriptions."""

from dataclasses import dataclass


@dataclass(frozen=True)
class ArchiveEntry:
    """A named source object or inline metadata entry in an archive."""

    filename: str
    object_key: str | None = None
    content: bytes = b""
