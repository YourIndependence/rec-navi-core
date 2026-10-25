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
from collections.abc import Sequence

from recnavi.core.types.archive_entry import ArchiveEntry


class BaseObjectStorage(ABC):
    """Abstract object storage for recorded media."""

    @abstractmethod
    async def upload_base64(
        self,
        *,
        object_key: str,
        base64_data: str,
        content_type: str = "video/mp4",
    ) -> None:
        """Decode base64 data and store it as an object."""
        pass

    @abstractmethod
    async def delete_objects_by_prefix(
        self,
        *,
        prefix: str,
    ) -> int:
        """Delete all object whose key starts with the prefix."""
        pass

    @abstractmethod
    async def delete_object_by_key(
        self,
        *,
        object_key: str,
    ) -> None:
        """Delete one object by its exact key."""
        pass

    @abstractmethod
    async def download_object(
        self,
        *,
        object_key: str,
    ) -> bytes:
        """Download an object as bytes."""
        pass

    @abstractmethod
    def download_object_stream(
        self,
        *,
        object_key: str,
    ) -> AsyncIterator[bytes]:
        """Stream an object's content as byte chunks."""
        pass

    @abstractmethod
    async def generate_presigned_url(
        self,
        *,
        object_key: str,
        expiration: int = 3600,
    ) -> str:
        """Generate a presigned download URL for an object."""
        pass

    @abstractmethod
    async def create_archive(
        self,
        *,
        object_key: str,
        entries: Sequence[ArchiveEntry],
    ) -> None:
        """Store a ZIP from source objects and metadata with bounded memory."""
        pass
