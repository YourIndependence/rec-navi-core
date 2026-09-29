# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.

"""Tests for get_scene_thumbnail_usecase."""

from unittest.mock import AsyncMock
from unittest.mock import patch

import pytest

from recnavi.application.scene.get_scene_thumbnail_usecase import (
    get_scene_thumbnail_usecase,
)
from recnavi.core.types.scene_master import SceneMaster
from recnavi.exceptions.exceptions import ClientResourcesNotFoundError
from recnavi.exceptions.exceptions import ClientUnprocessableEntityError
from tests.mockups.mock_database import MockDatabase


@pytest.mark.asyncio
async def test_usecase_delegates_to_get_scene_master_by_principal():
    """Test usecase delegates to core get_scene_master_by_principal collaborator."""
    mock_db = MockDatabase()

    expected_scene_master = SceneMaster(
        scene_principal="cooking",
        title="Cooking Scene",
        thumbnail_uri="scenes/cooking/example.jpg",
        guide_uri="scenes/cooking/guide.png",
        max_duration_seconds=60,
    )

    class MockStreamingBody:
        def __aiter__(self):
            return self

        async def __anext__(self):
            raise StopAsyncIteration

    with (
        patch(
            "recnavi.application.scene.get_scene_thumbnail_usecase.get_scene_master_by_principal",
            new=AsyncMock(return_value=expected_scene_master),
        ) as mock_get_scene,
        patch(
            "recnavi.application.scene.get_scene_thumbnail_usecase.download_object_stream",
            return_value=MockStreamingBody(),
        ),
    ):
        _, content_type = await get_scene_thumbnail_usecase(
            scenes_db=mock_db,
            scene_principal="cooking",
            kind="example",
            bucket_name="test-bucket",
        )

    mock_get_scene.assert_awaited_once_with(
        scenes_db=mock_db,
        scene_principal="cooking",
    )
    assert content_type == "image/jpeg"


@pytest.mark.asyncio
async def test_usecase_returns_thumbnail_stream_and_content_type():
    """Test usecase returns byte stream and content type for example image."""
    mock_db = MockDatabase(
        initial_items=[
            {
                "scenePrincipal": "cooking",
                "title": "Cooking Scene",
                "thumbnailUri": "scenes/cooking/example.jpg",
                "guideUri": "scenes/cooking/guide.png",
                "maxDurationSeconds": 60,
            },
        ],
    )

    # Mock async iterator for S3 stream
    class MockStreamingBody:
        def __aiter__(self):
            return self

        async def __anext__(self):
            if not hasattr(self, "_yielded"):
                self._yielded = True
                return b"fake image bytes"
            raise StopAsyncIteration

    with patch(
        "recnavi.application.scene.get_scene_thumbnail_usecase.download_object_stream",
    ) as mock_download:
        mock_download.return_value = MockStreamingBody()

        stream, content_type = await get_scene_thumbnail_usecase(
            scenes_db=mock_db,
            scene_principal="cooking",
            kind="example",
            bucket_name="test-bucket",
        )

        chunks = []
        async for chunk in stream:
            chunks.append(chunk)

        assert b"".join(chunks) == b"fake image bytes"
        assert content_type == "image/jpeg"
        mock_download.assert_called_once_with(
            bucket_name="test-bucket",
            object_key="scenes/cooking/example.jpg",
        )


@pytest.mark.asyncio
async def test_usecase_returns_guide_stream_and_content_type():
    """Test usecase returns byte stream and content type for guide image."""
    mock_db = MockDatabase(
        initial_items=[
            {
                "scenePrincipal": "cooking",
                "title": "Cooking Scene",
                "thumbnailUri": "scenes/cooking/example.jpg",
                "guideUri": "scenes/cooking/guide.png",
                "maxDurationSeconds": 60,
            },
        ],
    )

    class MockStreamingBody:
        def __aiter__(self):
            return self

        async def __anext__(self):
            if not hasattr(self, "_yielded"):
                self._yielded = True
                return b"fake guide image"
            raise StopAsyncIteration

    with patch(
        "recnavi.application.scene.get_scene_thumbnail_usecase.download_object_stream",
    ) as mock_download:
        mock_download.return_value = MockStreamingBody()

        stream, content_type = await get_scene_thumbnail_usecase(
            scenes_db=mock_db,
            scene_principal="cooking",
            kind="guide",
            bucket_name="test-bucket",
        )

        chunks = []
        async for chunk in stream:
            chunks.append(chunk)

        assert b"".join(chunks) == b"fake guide image"
        assert content_type == "image/png"
        mock_download.assert_called_once_with(
            bucket_name="test-bucket",
            object_key="scenes/cooking/guide.png",
        )


@pytest.mark.asyncio
async def test_usecase_raises_404_when_scene_not_found():
    """Test usecase raises ClientResourcesNotFoundError when scene doesn't exist."""
    mock_db = MockDatabase(initial_items=[])

    with pytest.raises(ClientResourcesNotFoundError):
        await get_scene_thumbnail_usecase(
            scenes_db=mock_db,
            scene_principal="nonexistent",
            kind="example",
            bucket_name="test-bucket",
        )


@pytest.mark.asyncio
async def test_usecase_raises_422_for_invalid_kind():
    """Test usecase raises ClientUnprocessableEntityError for invalid kind."""
    mock_db = MockDatabase(
        initial_items=[
            {
                "scenePrincipal": "cooking",
                "title": "Cooking Scene",
                "thumbnailUri": "scenes/cooking/example.jpg",
                "guideUri": "scenes/cooking/guide.png",
                "maxDurationSeconds": 60,
            },
        ],
    )

    with pytest.raises(ClientUnprocessableEntityError):
        await get_scene_thumbnail_usecase(
            scenes_db=mock_db,
            scene_principal="cooking",
            kind="invalid_kind",
            bucket_name="test-bucket",
        )


@pytest.mark.asyncio
async def test_usecase_infers_jpeg_content_type_from_extension():
    """Test usecase infers image/jpeg from .jpg extension."""
    mock_db = MockDatabase(
        initial_items=[
            {
                "scenePrincipal": "serving",
                "title": "Serving Scene",
                "thumbnailUri": "scenes/serving/photo.jpeg",
                "guideUri": "scenes/serving/overlay.png",
                "maxDurationSeconds": 30,
            },
        ],
    )

    class MockStreamingBody:
        def __aiter__(self):
            return self

        async def __anext__(self):
            raise StopAsyncIteration

    with patch(
        "recnavi.application.scene.get_scene_thumbnail_usecase.download_object_stream",
    ) as mock_download:
        mock_download.return_value = MockStreamingBody()

        _, content_type = await get_scene_thumbnail_usecase(
            scenes_db=mock_db,
            scene_principal="serving",
            kind="example",
            bucket_name="test-bucket",
        )

        assert content_type == "image/jpeg"


@pytest.mark.asyncio
async def test_usecase_infers_png_content_type_from_extension():
    """Test usecase infers image/png from .png extension."""
    mock_db = MockDatabase(
        initial_items=[
            {
                "scenePrincipal": "serving",
                "title": "Serving Scene",
                "thumbnailUri": "scenes/serving/photo.jpg",
                "guideUri": "scenes/serving/overlay.png",
                "maxDurationSeconds": 30,
            },
        ],
    )

    class MockStreamingBody:
        def __aiter__(self):
            return self

        async def __anext__(self):
            raise StopAsyncIteration

    with patch(
        "recnavi.application.scene.get_scene_thumbnail_usecase.download_object_stream",
    ) as mock_download:
        mock_download.return_value = MockStreamingBody()

        _, content_type = await get_scene_thumbnail_usecase(
            scenes_db=mock_db,
            scene_principal="serving",
            kind="guide",
            bucket_name="test-bucket",
        )

        assert content_type == "image/png"
