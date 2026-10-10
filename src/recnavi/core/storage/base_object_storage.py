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
from collections.abc import AsyncIterator


class BaseObjectStorage(ABC):
    """Abstract object storage for recorded media."""

    @abstractmethod
    def download_object_stream(
        self,
        *,
        bucket_name: str,
        object_key: str,
    ) -> AsyncIterator[bytes]:
        """Stream an object's content as byte chunks.

        Args:
            bucket_name: Bucket to read from.
            object_key: Key of the object.

        Returns:
            Async iterator of byte chunks.

        """
        pass
