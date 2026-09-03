# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.


"""Assets stored in S3."""

import asyncio

from botocore.exceptions import ClientError

from recnavi.core.repositories.asset_storage import BaseAssetStorage
from recnavi.infrastructure.s3.client import get_client


class S3AssetStorage(BaseAssetStorage):
    """Assets read from the media bucket."""

    def __init__(self, *, bucket_name: str) -> None:
        self._bucket_name = bucket_name

    async def read(self, *, key: str) -> bytes | None:
        """Return the stored bytes, or nothing when there is no object."""
        return await asyncio.to_thread(self._read, key)

    def _read(self, key: str) -> bytes | None:
        """Fetch one object, treating a missing one as an answer."""
        try:
            response = get_client().get_object(
                Bucket=self._bucket_name,
                Key=key,
            )
        except ClientError as e:
            if e.response["Error"]["Code"] in {"NoSuchKey", "404"}:
                return None
            raise
        return response["Body"].read()
