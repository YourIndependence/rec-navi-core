# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.

"""S3 client for presigned URL generation and object operations."""

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
    """Generate presigned URL for S3 object."""
    session = aioboto3.Session()
    async with session.client("s3", region_name=REGION) as s3:
        url = s3.generate_presigned_url(
            ClientMethod="get_object",
            Params={"Bucket": bucket_name, "Key": object_key},
            ExpiresIn=expiration,
        )
        return url


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
