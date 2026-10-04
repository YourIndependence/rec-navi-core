# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.

"""S3 client for presigned URL generation and object deletion."""

import base64

import aioboto3

from recnavi.config.variables import REGION


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
        prefix: Object key prefix (e.g., "projects/proj-123/").

    Returns:
        Number of objects deleted.

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

            contents = response.get("Contents", [])
            if not contents:
                break

            delete_keys = [{"Key": obj["Key"]} for obj in contents]

            await s3.delete_objects(
                Bucket=bucket_name,
                Delete={"Objects": delete_keys},
            )

            deleted_count += len(delete_keys)

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
    except Exception as e:
        raise ValueError("Invalid base64 data") from e

    session = aioboto3.Session()
    async with session.client("s3", region_name=REGION) as s3:
        await s3.put_object(
            Bucket=bucket_name,
            Key=object_key,
            Body=binary_data,
            ContentType=content_type,
        )
