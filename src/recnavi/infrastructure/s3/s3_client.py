# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.

"""S3 client for presigned URL generation and object streaming."""

from collections.abc import AsyncIterator

import aioboto3

from recnavi.config.variables import REGION
from recnavi.core.storage.base_object_storage import BaseObjectStorage


async def generate_presigned_url(
    bucket_name: str,
    object_key: str,
    expiration: int = 3600,
) -> str:
    """Generate presigned URL for S3 object.

    Args:
        bucket_name: S3 bucket name.
        object_key: S3 object key (e.g., "videos/scene-123.mp4").
        expiration: URL expiration time in seconds (default 3600 = 1 hour).

    Returns:
        Presigned URL string.

    """
    session = aioboto3.Session()
    async with session.client("s3", region_name=REGION) as s3:
        url = s3.generate_presigned_url(
            ClientMethod="get_object",
            Params={"Bucket": bucket_name, "Key": object_key},
            ExpiresIn=expiration,
        )
        return url


async def download_object_stream(
    *,
    bucket_name: str,
    object_key: str,
) -> AsyncIterator[bytes]:
    """Download S3 object as async byte stream.

    Args:
        bucket_name: S3 bucket name.
        object_key: S3 object key (e.g., "scenes/cooking/thumbnail.jpg").

    Yields:
        Byte chunks from S3 object.

    Raises:
        ClientError: If S3 object not found or access denied.

    """
    session = aioboto3.Session()
    async with session.client("s3", region_name=REGION) as s3:
        response = await s3.get_object(Bucket=bucket_name, Key=object_key)
        async for chunk in response["Body"]:
            yield chunk


class S3Client(BaseObjectStorage):
    """S3 implementation of the object storage."""

    def download_object_stream(
        self,
        *,
        bucket_name: str,
        object_key: str,
    ) -> AsyncIterator[bytes]:
        """Stream an S3 object as byte chunks."""
        return download_object_stream(
            bucket_name=bucket_name,
            object_key=object_key,
        )
