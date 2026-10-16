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

    @abstractmethod
    async def delete_objects_by_prefix(
        self,
        *,
        bucket_name: str,
        prefix: str,
    ) -> int:
        """Delete every object whose key starts with the prefix.

        Args:
            bucket_name: Bucket to delete from.
            prefix: Key prefix to match.

        Returns:
            Number of deleted objects.

        """
        pass

    @abstractmethod
    async def delete_object_by_key(
        self,
        *,
        bucket_name: str,
        object_key: str,
    ) -> None:
        """Delete one object by its exact key."""
        pass

    @abstractmethod
    async def download_object(
        self,
        *,
        bucket_name: str,
        object_key: str,
    ) -> bytes:
        """Download an object as bytes.

        Args:
            bucket_name: Bucket to read from.
            object_key: Key of the object.

        Returns:
            Object content as bytes.

        """
        pass

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
            Async iterator yielding the object content in chunks.

        """
        pass

    @abstractmethod
    async def generate_presigned_url(
        self,
        *,
        bucket_name: str,
        object_key: str,
        expiration: int = 3600,
    ) -> str:
        """Generate a presigned download URL for an object.

        Args:
            bucket_name: Bucket containing the object.
            object_key: Key of the object.
            expiration: URL expiration time in seconds.

        Returns:
            Presigned URL string.

        """
        pass
