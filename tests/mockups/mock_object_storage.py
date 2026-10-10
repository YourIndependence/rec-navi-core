# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.

"""Mock object storage for unit testing."""

import base64

from recnavi.core.storage.base_object_storage import BaseObjectStorage


class MockObjectStorage(BaseObjectStorage):
    """In-memory object storage for unit testing."""

    def __init__(self) -> None:
        """Initialize an empty storage."""
        self.objects: dict[tuple[str, str], tuple[bytes, str]] = {}

    async def upload_base64(
        self,
        *,
        bucket_name: str,
        object_key: str,
        base64_data: str,
        content_type: str,
    ) -> None:
        """Store the decoded content in memory."""
        try:
            data = base64.b64decode(base64_data, validate=True)
        except ValueError as e:
            raise ValueError("Invalid base64 data") from e
        self.objects[(bucket_name, object_key)] = (data, content_type)

    async def download_object(
        self,
        *,
        bucket_name: str,
        object_key: str,
    ) -> bytes:
        """Return the stored content."""
        return self.objects[(bucket_name, object_key)][0]

    async def generate_presigned_url(
        self,
        *,
        bucket_name: str,
        object_key: str,
        expiration: int = 3600,
    ) -> str:
        """Return a deterministic fake URL."""
        return f"mock://{bucket_name}/{object_key}?expires={expiration}"
