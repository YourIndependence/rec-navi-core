# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.

"""S3 client for presigned URLs and object transfer."""

import base64
import binascii
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


async def delete_objects_by_prefix(
    *,
    bucket_name: str,
    prefix: str,
) -> int:
    """Delete all S3 objects under a prefix.

    Args:
        bucket_name: S3 bucket name.
        prefix: Key prefix to match (e.g., "projects/proj-123/").

    Returns:
        Number of deleted objects.

    """
    session = aioboto3.Session()
    deleted_count = 0

    async with session.client("s3", region_name=REGION) as s3:
        continuation_token = None

        while True:
            list_kwargs = {
                "Bucket": bucket_name,
                "Prefix": prefix,
            }
            if continuation_token:
                list_kwargs["ContinuationToken"] = continuation_token

            response = await s3.list_objects_v2(**list_kwargs)

            if "Contents" not in response:
                break

            objects_to_delete = [
                {"Key": obj["Key"]} for obj in response["Contents"]
            ]

            if objects_to_delete:
                await s3.delete_objects(
                    Bucket=bucket_name,
                    Delete={"Objects": objects_to_delete},
                )
                deleted_count += len(objects_to_delete)

            if not response.get("IsTruncated"):
                break

            continuation_token = response.get("NextContinuationToken")

    return deleted_count


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

    async def delete_objects_by_prefix(
        self,
        *,
        bucket_name: str,
        prefix: str,
    ) -> int:
        """Delete all S3 objects under a prefix."""
        return await delete_objects_by_prefix(
            bucket_name=bucket_name,
            prefix=prefix,
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

    def download_object_stream(
        self,
        *,
        bucket_name: str,
        object_key: str,
    ) -> AsyncIterator[bytes]:
        """Stream an S3 object's content as byte chunks."""
        return download_object_stream(
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
