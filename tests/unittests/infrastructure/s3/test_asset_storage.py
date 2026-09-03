# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.

"""Unit tests for the S3 asset storage."""

import boto3
import pytest
from moto import mock_aws

from recnavi.core.repositories.asset_storage import BaseAssetStorage
from recnavi.infrastructure.s3.asset_storage import S3AssetStorage


BUCKET_NAME = "recnavi-test-media"
KEY = "assets/scenes/shop_gaikan/example.jpg"


def _create_bucket():
    """Create the media bucket the way the infrastructure defines it."""
    client = boto3.client("s3", region_name="ap-northeast-1")
    client.create_bucket(
        Bucket=BUCKET_NAME,
        CreateBucketConfiguration={
            "LocationConstraint": "ap-northeast-1",
        },
    )
    return client


@pytest.mark.asyncio
async def test_reads_a_stored_object():
    """The bytes come back exactly as they were stored."""
    with mock_aws():
        client = _create_bucket()
        client.put_object(Bucket=BUCKET_NAME, Key=KEY, Body=b"\xff\xd8jpeg")

        content = await S3AssetStorage(bucket_name=BUCKET_NAME).read(key=KEY)

    assert content == b"\xff\xd8jpeg"


@pytest.mark.asyncio
async def test_answers_nothing_for_a_missing_object():
    """A missing object is not an error the caller has to catch."""
    with mock_aws():
        _create_bucket()

        content = await S3AssetStorage(bucket_name=BUCKET_NAME).read(
            key="assets/scenes/nowhere/example.jpg",
        )

    assert content is None


def test_implements_the_core_abstraction():
    """The application layer only ever sees the abstraction."""
    assert issubclass(S3AssetStorage, BaseAssetStorage)
