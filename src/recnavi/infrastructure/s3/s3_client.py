# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.

"""S3 client for presigned URL generation."""

import aioboto3

from recnavi.config.variables import REGION


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
