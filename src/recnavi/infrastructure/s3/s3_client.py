# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.

"""S3 implementation of the object storage abstraction."""

import base64
import binascii
from collections.abc import AsyncIterator

import aioboto3

from recnavi.config.variables import REGION
from recnavi.core.storage.base_object_storage import BaseObjectStorage


class S3Client(BaseObjectStorage):
    """S3 object storage bound to one bucket."""

    def __init__(self, bucket_name: str) -> None:
        self.bucket_name = bucket_name
        self.session = aioboto3.Session(region_name=REGION)

    async def generate_presigned_url(
        self,
        *,
        object_key: str,
        expiration: int = 3600,
    ) -> str:
        """Generate a presigned URL for an S3 object."""
        async with self.session.client("s3") as s3:
            return await s3.generate_presigned_url(
                ClientMethod="get_object",
                Params={"Bucket": self.bucket_name, "Key": object_key},
                ExpiresIn=expiration,
            )

    async def delete_objects_by_prefix(self, *, prefix: str) -> int:
        """Delete all S3 objects under a prefix and return their count."""
        deleted_count = 0

        async with self.session.client("s3") as s3:
            continuation_token: str | None = None

            while True:
                list_kwargs = {
                    "Bucket": self.bucket_name,
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
                        Bucket=self.bucket_name,
                        Delete={"Objects": objects_to_delete},
                    )
                    deleted_count += len(objects_to_delete)

                if not response.get("IsTruncated"):
                    break
                continuation_token = response.get("NextContinuationToken")

        return deleted_count

    async def delete_object_by_key(self, *, object_key: str) -> None:
        """Delete one S3 object by its exact key."""
        async with self.session.client("s3") as s3:
            await s3.delete_object(Bucket=self.bucket_name, Key=object_key)

    async def upload_base64(
        self,
        *,
        object_key: str,
        base64_data: str,
        content_type: str = "video/mp4",
    ) -> None:
        """Upload base64-encoded data to S3."""
        try:
            binary_data = base64.b64decode(base64_data, validate=True)
        except binascii.Error as e:
            raise ValueError("Invalid base64 data") from e

        async with self.session.client("s3") as s3:
            await s3.put_object(
                Bucket=self.bucket_name,
                Key=object_key,
                Body=binary_data,
                ContentType=content_type,
            )

    async def download_object(self, *, object_key: str) -> bytes:
        """Download an S3 object as bytes."""
        async with self.session.client("s3") as s3:
            response = await s3.get_object(
                Bucket=self.bucket_name,
                Key=object_key,
            )
            return await response["Body"].read()

    async def download_object_stream(
        self,
        *,
        object_key: str,
    ) -> AsyncIterator[bytes]:
        """Download an S3 object's content as byte chunks."""
        async with self.session.client("s3") as s3:
            response = await s3.get_object(
                Bucket=self.bucket_name,
                Key=object_key,
            )
            async for chunk in response["Body"]:
                yield chunk
