# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.

"""S3 adapter behavior against Moto's in-memory AWS backend."""

import base64
import io
import time
import zipfile
from collections.abc import AsyncIterator
from urllib.parse import parse_qs
from urllib.parse import urlsplit

import aioboto3
import pytest
import pytest_asyncio
from botocore.exceptions import ClientError

from recnavi.config.variables import REGION
from recnavi.core.types.archive_entry import ArchiveEntry
from recnavi.infrastructure.s3.s3_client import S3Client


BUCKET = "it-media"
OTHER_BUCKET = "it-other-media"


@pytest_asyncio.fixture(scope="module")
async def buckets(mock_aws_session: aioboto3.Session) -> AsyncIterator[None]:
    async with mock_aws_session.client("s3") as s3:
        for bucket in (BUCKET, OTHER_BUCKET):
            await s3.create_bucket(
                Bucket=bucket,
                CreateBucketConfiguration={"LocationConstraint": REGION},
            )
    try:
        yield
    finally:
        async with mock_aws_session.client("s3") as s3:
            for bucket in (BUCKET, OTHER_BUCKET):
                paginator = s3.get_paginator("list_objects_v2")
                async for page in paginator.paginate(Bucket=bucket):
                    for item in page.get("Contents", []):
                        await s3.delete_object(Bucket=bucket, Key=item["Key"])
                await s3.delete_bucket(Bucket=bucket)


@pytest.fixture
def storage(buckets, mock_aws_session: aioboto3.Session) -> S3Client:
    storage = S3Client(bucket_name=BUCKET)
    storage.session = mock_aws_session
    return storage


def test_client_keeps_bucket_and_regional_session(mock_aws_session):
    storage = S3Client(bucket_name=BUCKET)
    created_session = storage.session
    storage.session = mock_aws_session
    assert storage.bucket_name == BUCKET
    assert isinstance(created_session, aioboto3.Session)
    assert created_session.region_name == REGION


@pytest.mark.asyncio
async def test_upload_stores_decoded_bytes_and_content_type(storage):
    await storage.upload_base64(
        object_key="upload/video.mp4",
        base64_data=base64.b64encode(b"video-payload").decode(),
        content_type="video/webm",
    )
    async with storage.session.client("s3") as s3:
        response = await s3.get_object(Bucket=BUCKET, Key="upload/video.mp4")
        assert await response["Body"].read() == b"video-payload"
        assert response["ContentType"] == "video/webm"


@pytest.mark.asyncio
@pytest.mark.parametrize("base64_data", ["abc", "!!!!"])
async def test_invalid_base64_leaves_no_object(storage, base64_data):
    with pytest.raises(ValueError, match="Invalid base64 data"):
        await storage.upload_base64(
            object_key="invalid/video.mp4",
            base64_data=base64_data,
        )
    async with storage.session.client("s3") as s3:
        result = await s3.list_objects_v2(Bucket=BUCKET, Prefix="invalid/")
        assert result.get("Contents", []) == []


@pytest.mark.asyncio
async def test_download_returns_stored_bytes(storage):
    async with storage.session.client("s3") as s3:
        await s3.put_object(
            Bucket=BUCKET,
            Key="download/video.mp4",
            Body=b"video",
        )
    assert (
        await storage.download_object(object_key="download/video.mp4")
        == b"video"
    )


@pytest.mark.asyncio
async def test_stream_preserves_all_bytes_across_chunks(storage):
    payload = bytes(range(256)) * 8193
    async with storage.session.client("s3") as s3:
        await s3.put_object(
            Bucket=BUCKET,
            Key="stream/video.mp4",
            Body=payload,
        )
    chunks = [
        chunk
        async for chunk in storage.download_object_stream(
            object_key="stream/video.mp4",
        )
    ]
    assert len(chunks) > 1
    assert b"".join(chunks) == payload


@pytest.mark.asyncio
async def test_delete_by_key_preserves_other_objects(storage):
    async with storage.session.client("s3") as s3:
        for key in ("exact/video.mp4", "exact/video_thumb.jpg"):
            await s3.put_object(Bucket=BUCKET, Key=key, Body=b"recording")
    await storage.delete_object_by_key(object_key="exact/video.mp4")
    async with storage.session.client("s3") as s3:
        result = await s3.list_objects_v2(Bucket=BUCKET, Prefix="exact/")
        assert [item["Key"] for item in result["Contents"]] == [
            "exact/video_thumb.jpg",
        ]


@pytest.mark.asyncio
async def test_delete_prefix_removes_all_pages_and_preserves_other_data(
    storage,
    monkeypatch,
):
    monkeypatch.setenv("MOTO_S3_DEFAULT_MAX_KEYS", "2")
    async with storage.session.client("s3") as s3:
        for number in range(5):
            await s3.put_object(
                Bucket=BUCKET,
                Key=f"pages/{number}",
                Body=b"data",
            )
        await s3.put_object(Bucket=BUCKET, Key="outside/keep", Body=b"keep")
        await s3.put_object(
            Bucket=OTHER_BUCKET,
            Key="pages/keep",
            Body=b"keep",
        )
    assert await storage.delete_objects_by_prefix(prefix="pages/") == 5
    async with storage.session.client("s3") as s3:
        result = await s3.list_objects_v2(Bucket=BUCKET, Prefix="pages/")
        assert result.get("Contents", []) == []
        for bucket, key in (
            (BUCKET, "outside/keep"),
            (OTHER_BUCKET, "pages/keep"),
        ):
            result = await s3.get_object(Bucket=bucket, Key=key)
            assert await result["Body"].read() == b"keep"


@pytest.mark.asyncio
async def test_delete_empty_prefix_returns_zero(storage):
    assert await storage.delete_objects_by_prefix(prefix="missing/") == 0


@pytest.mark.asyncio
@pytest.mark.parametrize("expiration", [3600, 600])
async def test_presigned_url_identifies_object_and_expiration(
    storage,
    expiration,
):
    before = int(time.time())
    url = await storage.generate_presigned_url(
        object_key="videos/scene-1.mp4",
        expiration=expiration,
    )
    after = int(time.time())
    assert isinstance(url, str)
    parsed = urlsplit(url)
    query = parse_qs(parsed.query)
    assert parsed.scheme == "https"
    assert parsed.hostname.startswith(f"{BUCKET}.")
    assert parsed.path == "/videos/scene-1.mp4"
    if "X-Amz-Expires" in query:
        assert query["X-Amz-Expires"] == [str(expiration)]
        assert query["X-Amz-Signature"][0]
    else:
        assert (
            before + expiration
            <= int(query["Expires"][0])
            <= after + expiration
        )
        assert query["Signature"][0]


@pytest.mark.asyncio
async def test_missing_object_propagates_s3_error(storage):
    with pytest.raises(ClientError) as exc_info:
        await storage.download_object(object_key="missing/video.mp4")
    assert exc_info.value.response["Error"]["Code"] == "NoSuchKey"


@pytest.mark.asyncio
async def test_missing_bucket_propagates_s3_error(buckets, mock_aws_session):
    storage = S3Client(bucket_name="it-missing-media")
    storage.session = mock_aws_session
    with pytest.raises(ClientError) as exc_info:
        await storage.upload_base64(object_key="video.mp4", base64_data="eA==")
    assert exc_info.value.response["Error"]["Code"] == "NoSuchBucket"


@pytest.mark.asyncio
async def test_archive_round_trip_spans_multiple_upload_parts(storage):
    content = b"x" * (9 * 1024 * 1024)
    async with storage.session.client("s3") as s3:
        await s3.put_object(
            Bucket=BUCKET,
            Key="archive-source/video.mp4",
            Body=content,
        )
    await storage.create_archive(
        object_key="archives/multipart.zip",
        entries=[
            ArchiveEntry(
                filename="01_video.mp4",
                object_key="archive-source/video.mp4",
            ),
            ArchiveEntry(filename="metadata.json", content=b"{}"),
        ],
    )
    async with storage.session.client("s3") as s3:
        result = await s3.get_object(
            Bucket=BUCKET,
            Key="archives/multipart.zip",
        )
        assert result["ContentType"] == "application/zip"
        archive_bytes = await result["Body"].read()
        assert (await s3.list_multipart_uploads(Bucket=BUCKET)).get(
            "Uploads",
            [],
        ) == []
    with zipfile.ZipFile(io.BytesIO(archive_bytes)) as archive:
        assert archive.read("01_video.mp4") == content
        assert archive.read("metadata.json") == b"{}"


@pytest.mark.asyncio
async def test_archive_empty_source_and_inline_content(storage):
    async with storage.session.client("s3") as s3:
        await s3.put_object(
            Bucket=BUCKET,
            Key="archive-source/empty.mp4",
            Body=b"",
        )
    await storage.create_archive(
        object_key="archives/empty.zip",
        entries=[
            ArchiveEntry(
                filename="empty.mp4",
                object_key="archive-source/empty.mp4",
            ),
        ],
    )
    with zipfile.ZipFile(
        io.BytesIO(
            await storage.download_object(object_key="archives/empty.zip"),
        ),
    ) as archive:
        assert archive.read("empty.mp4") == b""


@pytest.mark.asyncio
async def test_archive_aborts_failed_multipart_upload(storage):
    def fail_upload_part(**kwargs):
        raise RuntimeError("upload failed")

    storage.session.events.register(
        "before-call.s3.UploadPart",
        fail_upload_part,
    )
    try:
        with pytest.raises(RuntimeError, match="upload failed"):
            await storage.create_archive(
                object_key="archives/failed.zip",
                entries=[
                    ArchiveEntry(filename="metadata.json", content=b"{}"),
                ],
            )
        async with storage.session.client("s3") as s3:
            assert (await s3.list_multipart_uploads(Bucket=BUCKET)).get(
                "Uploads",
                [],
            ) == []
            assert (
                await s3.list_objects_v2(
                    Bucket=BUCKET,
                    Prefix="archives/failed.zip",
                )
            ).get("Contents", []) == []
    finally:
        storage.session.events.unregister(
            "before-call.s3.UploadPart",
            fail_upload_part,
        )


@pytest.mark.asyncio
async def test_archive_ignores_empty_chunks(storage, monkeypatch):
    async def chunks(*, object_key):
        yield b""
        yield b"video"
        yield b""

    monkeypatch.setattr(storage, "download_object_stream", chunks)
    await storage.create_archive(
        object_key="archives/chunks.zip",
        entries=[ArchiveEntry(filename="video.mp4", object_key="source")],
    )
    with zipfile.ZipFile(
        io.BytesIO(
            await storage.download_object(object_key="archives/chunks.zip"),
        ),
    ) as archive:
        assert archive.read("video.mp4") == b"video"


@pytest.mark.asyncio
async def test_archive_source_failure_publishes_nothing(storage):
    with pytest.raises(ClientError):
        await storage.create_archive(
            object_key="archives/missing-source.zip",
            entries=[
                ArchiveEntry(
                    filename="video.mp4",
                    object_key="does-not-exist.mp4",
                ),
            ],
        )
    async with storage.session.client("s3") as s3:
        assert (await s3.list_multipart_uploads(Bucket=BUCKET)).get(
            "Uploads",
            [],
        ) == []
        assert (
            await s3.list_objects_v2(
                Bucket=BUCKET,
                Prefix="archives/missing-source.zip",
            )
        ).get("Contents", []) == []
