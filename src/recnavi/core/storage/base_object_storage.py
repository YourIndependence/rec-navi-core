# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.

"""Object storage abstraction."""

from abc import ABC
from abc import abstractmethod


class BaseObjectStorage(ABC):
    """Abstract object storage for recorded media."""

    @abstractmethod
    async def generate_presigned_url(
        self,
        *,
        bucket_name: str,
        object_key: str,
        expiration: int = 3600,
    ) -> str:
        """Generate a presigned GET URL for an object.

        Args:
            bucket_name: Bucket holding the object.
            object_key: Key of the object.
            expiration: URL lifetime in seconds.

        Returns:
            Presigned URL string.

        """
        pass
