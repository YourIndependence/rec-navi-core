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
import io
import zipfile
from collections.abc import AsyncIterator
from collections.abc import Sequence

from recnavi.core.storage.base_object_storage import BaseObjectStorage
from recnavi.core.types.archive_entry import ArchiveEntry


class MockObjectStorage(BaseObjectStorage):
    """In-memory object storage for unit testing."""

    def __init__(self, bucket_name: str) -> None:
        """Initialize an empty storage."""
        self.bucket_name = bucket_name
        self.objects: dict[tuple[str, str], tuple[bytes, str]] = {}

    async def upload_base64(
        self,
        *,
        object_key: str,
        base64_data: str,
        content_type: str = "video/mp4",
    ) -> None:
        """Store the decoded content in memory."""
        try:
            data = base64.b64decode(base64_data, validate=True)
        except binascii.Error as e:
            raise ValueError("Invalid base64 data") from e
        self.objects[(self.bucket_name, object_key)] = (data, content_type)

    async def delete_objects_by_prefix(
        self,
        *,
        prefix: str,
    ) -> int:
        """Remove every stored object whose key starts with the prefix."""
        doomed = [
            key
            for key in self.objects
            if key[0] == self.bucket_name and key[1].startswith(prefix)
        ]
        for key in doomed:
            del self.objects[key]
        return len(doomed)

    async def delete_object_by_key(
        self,
        *,
        object_key: str,
    ) -> None:
        """Remove one stored object by its exact key."""
        self.objects.pop((self.bucket_name, object_key), None)

    async def download_object(
        self,
        *,
        object_key: str,
    ) -> bytes:
        """Return the stored content."""
        return self.objects[(self.bucket_name, object_key)][0]

    async def download_object_stream(
        self,
        *,
        object_key: str,
    ) -> AsyncIterator[bytes]:
        """Yield the stored content as a single chunk."""
        yield self.objects[(self.bucket_name, object_key)][0]

    async def generate_presigned_url(
        self,
        *,
        object_key: str,
        expiration: int = 3600,
    ) -> str:
        """Return a deterministic fake URL."""
        return f"mock://{self.bucket_name}/{object_key}?expires={expiration}"

    async def create_archive(
        self,
        *,
        object_key: str,
        entries: Sequence[ArchiveEntry],
    ) -> None:
        """Build a small in-memory archive for isolated tests."""
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w", zipfile.ZIP_STORED) as archive:
            for entry in entries:
                content = (
                    await self.download_object(object_key=entry.object_key)
                    if entry.object_key is not None
                    else entry.content
                )
                archive.writestr(entry.filename, content)
        self.objects[(self.bucket_name, object_key)] = (
            buffer.getvalue(),
            "application/zip",
        )
