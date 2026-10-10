# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.

"""S3 client for presigned URL generation and object transfer."""

import base64
import binascii

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


async def upload_base64(
    *,
    bucket_name: str,
    object_key: str,
    base64_data: str,
    content_type: str = "video/mp4",
) -> None:
    """Upload base64-encoded data to S3.

    Args:
        bucket_name: S3 bucket name.
        object_key: S3 object key (e.g., "projects/proj-123/scenes/scene-1/shot-abc.mp4").
        base64_data: Base64-encoded binary data.
        content_type: MIME type for Content-Type header.

    Raises:
        ValueError: Invalid base64 data.

    """
    try:
        binary_data = base64.b64decode(base64_data)
    except binascii.Error as e:
        raise ValueError("Invalid base64 data") from e

    session = aioboto3.Session()
    async with session.client("s3", region_name=REGION) as s3:
        await s3.put_object(
            Bucket=bucket_name,
            Key=object_key,
            Body=binary_data,
            ContentType=content_type,
        )


async def download_object(
    *,
    bucket_name: str,
    object_key: str,
) -> bytes:
    """Download S3 object as bytes.

    Args:
        bucket_name: S3 bucket name.
        object_key: S3 object key (e.g., "videos/scene-123.mp4").

    Returns:
        Object content as bytes.

    Raises:
        ClientError: If S3 object not found or access denied.

    """
    session = aioboto3.Session()
    async with session.client("s3", region_name=REGION) as s3:
        response = await s3.get_object(Bucket=bucket_name, Key=object_key)
        return await response["Body"].read()


class S3Client(BaseObjectStorage):
    """S3 implementation of the object storage."""

    async def upload_base64(
        self,
        *,
        bucket_name: str,
        object_key: str,
        base64_data: str,
        content_type: str,
    ) -> None:
        """Upload base64-encoded data to S3."""
        await upload_base64(
            bucket_name=bucket_name,
            object_key=object_key,
            base64_data=base64_data,
            content_type=content_type,
        )

    async def download_object(
        self,
        *,
        bucket_name: str,
        object_key: str,
    ) -> bytes:
        """Download an S3 object as bytes."""
        return await download_object(
            bucket_name=bucket_name,
            object_key=object_key,
        )

    async def generate_presigned_url(
        self,
        *,
        bucket_name: str,
        object_key: str,
        expiration: int = 3600,
    ) -> str:
        """Generate a presigned URL for an S3 object."""
        return await generate_presigned_url(
            bucket_name=bucket_name,
            object_key=object_key,
            expiration=expiration,
        )
