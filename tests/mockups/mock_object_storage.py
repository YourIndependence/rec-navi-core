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
    """In-memory mock object storage for unit testing."""

    async def generate_presigned_url(
        self,
        *,
        bucket_name: str,
        object_key: str,
        expiration: int = 3600,
    ) -> str:
        """Return a deterministic fake URL."""
        return f"mock://{bucket_name}/{object_key}?expires={expiration}"
