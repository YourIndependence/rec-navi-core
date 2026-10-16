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
import binascii
from collections.abc import AsyncIterator

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
        except binascii.Error as e:
            raise ValueError("Invalid base64 data") from e
        self.objects[(bucket_name, object_key)] = (data, content_type)

    async def delete_objects_by_prefix(
        self,
        *,
        bucket_name: str,
        prefix: str,
    ) -> int:
        """Remove every stored object whose key starts with the prefix."""
        doomed = [
            key
            for key in self.objects
            if key[0] == bucket_name and key[1].startswith(prefix)
        ]
        for key in doomed:
            del self.objects[key]
        return len(doomed)

    async def delete_object_by_key(
        self,
        *,
        bucket_name: str,
        object_key: str,
    ) -> None:
        """Remove one stored object by its exact key."""
        self.objects.pop((bucket_name, object_key), None)

    async def download_object(
        self,
        *,
        bucket_name: str,
        object_key: str,
    ) -> bytes:
        """Return the stored content."""
        return self.objects[(bucket_name, object_key)][0]

    async def download_object_stream(
        self,
        *,
        bucket_name: str,
        object_key: str,
    ) -> AsyncIterator[bytes]:
        """Yield the stored content as a single chunk."""
        yield self.objects[(bucket_name, object_key)][0]

    async def generate_presigned_url(
        self,
        *,
        bucket_name: str,
        object_key: str,
        expiration: int = 3600,
    ) -> str:
        """Return a deterministic fake URL."""
        return f"mock://{bucket_name}/{object_key}?expires={expiration}"
