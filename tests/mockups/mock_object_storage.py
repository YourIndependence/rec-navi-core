# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.

"""Mock object storage for unit testing."""

from collections.abc import AsyncIterator

from recnavi.core.storage.base_object_storage import BaseObjectStorage


class MockObjectStorage(BaseObjectStorage):
    """In-memory object storage for unit testing."""

    def __init__(self) -> None:
        """Initialize an empty storage."""
        self.objects: dict[tuple[str, str], tuple[bytes, str]] = {}

    async def download_object_stream(
        self,
        *,
        bucket_name: str,
        object_key: str,
    ) -> AsyncIterator[bytes]:
        """Yield the stored content as a single chunk."""
        data, _ = self.objects[(bucket_name, object_key)]
        yield data
