# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.

"""In-process AWS isolation shared by infrastructure unit tests."""

from collections.abc import Iterator

import aioboto3
import pytest
from moto import mock_aws
from moto.core.botocore_stubber import BotocoreStubber

from recnavi.config.variables import REGION
from tests.mockups.moto_async import async_moto_response


@pytest.fixture(scope="module")
def moto_aws() -> Iterator[None]:
    with pytest.MonkeyPatch.context() as patcher:
        for name, value in {
            "AWS_ACCESS_KEY_ID": "testing",
            "AWS_SECRET_ACCESS_KEY": "testing",
            "AWS_SESSION_TOKEN": "testing",
            "AWS_DEFAULT_REGION": "ap-northeast-1",
            "AWS_EC2_METADATA_DISABLED": "true",
        }.items():
            patcher.setenv(name, value)
        for name in (
            "AWS_PROFILE",
            "AWS_DEFAULT_PROFILE",
            "AWS_ENDPOINT_URL",
            "AWS_ENDPOINT_URL_S3",
            "AWS_ENDPOINT_URL_DYNAMODB",
        ):
            patcher.delenv(name, raising=False)
        patcher.setattr(BotocoreStubber, "__call__", async_moto_response)
        with mock_aws():
            yield


@pytest.fixture(scope="module")
def mock_aws_session(moto_aws) -> aioboto3.Session:
    return aioboto3.Session(
        aws_access_key_id="testing",
        aws_secret_access_key="testing",
        aws_session_token="testing",
        region_name=REGION,
    )
