# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.

"""Adapt Moto's synchronous HTTP bodies to aiobotocore's async transport."""

from typing import cast

from aiobotocore.awsrequest import AioAWSResponse
from aiobotocore.httpchecksum import AioAwsChunkedWrapper
from botocore.awsrequest import AWSPreparedRequest
from moto.core.botocore_stubber import BotocoreStubber
from moto.core.botocore_stubber import MockRawResponse


class AsyncMotoBody:
    """Expose Moto's real response bytes through an async stream."""

    def __init__(self, raw: MockRawResponse) -> None:
        self.raw = raw
        self.content = self

    async def read(self, size: int = -1) -> bytes:
        return self.raw.read(size)

    def at_eof(self) -> bool:
        return self.raw.tell() == len(self.raw.getbuffer())

    def close(self) -> None:
        self.raw.close()


_moto_response = BotocoreStubber.__call__


async def async_moto_response(
    stubber: BotocoreStubber,
    event_name: str,
    request: AWSPreparedRequest,
    **kwargs: object,
) -> AioAWSResponse | None:
    """Keep Moto request handling intact and adapt only the HTTP response."""
    if isinstance(request.body, AioAwsChunkedWrapper):
        request.body = await request.body.read()
    response = _moto_response(stubber, event_name, request, **kwargs)
    if response is None:
        raise AssertionError(f"Moto did not handle request: {request.url}")
    return AioAWSResponse(
        response.url,
        response.status_code,
        response.headers,
        AsyncMotoBody(cast(MockRawResponse, response.raw)),
    )
