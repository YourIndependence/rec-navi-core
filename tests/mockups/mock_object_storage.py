# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.

"""Mock object storage for unit testing."""

from recnavi.core.storage.base_object_storage import BaseObjectStorage


class MockObjectStorage(BaseObjectStorage):
    """In-memory object storage for unit testing."""

    def __init__(self) -> None:
        """Initialize an empty storage."""
        self.objects: dict[tuple[str, str], tuple[bytes, str]] = {}

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
