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
    async def upload_base64(
        self,
        *,
        bucket_name: str,
        object_key: str,
        base64_data: str,
        content_type: str,
    ) -> None:
        """Decode base64 data and store it as an object.

        Args:
            bucket_name: Bucket to write to.
            object_key: Key of the new object.
            base64_data: Base64-encoded content.
            content_type: MIME type of the content.

        Raises:
            ValueError: base64_data is not valid base64.

        """
        pass
