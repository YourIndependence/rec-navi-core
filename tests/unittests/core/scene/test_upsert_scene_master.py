# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or reproduction of this software is strictly prohibited.
#
# For internal use only.
# developer team.

"""Regression tests for scene master writes."""

from unittest.mock import AsyncMock

import pytest
from pydantic import ValidationError

from recnavi.core.scene.upsert_scene_master import update_scene_master
from recnavi.core.types.user import UserRole
from recnavi.exceptions.exceptions import ClientAuthorizationError
from recnavi.exceptions.exceptions import ClientUnprocessableEntityError
from tests.mockups.mock_database import MockDatabase
from tests.mockups.mock_object_storage import MockObjectStorage
from tests.mockups.mock_users import get_mock_x_user


@pytest.mark.asyncio
@pytest.mark.parametrize("role", [UserRole.STAFF, UserRole.OWNER])
async def test_non_admin_cannot_read_or_write_master(role):
    database = AsyncMock()
    storage = AsyncMock()
    with pytest.raises(ClientAuthorizationError):
        await update_scene_master(
            scenes_db=database,
            storage=storage,
            bucket_name="test-bucket",
            scene_principal="cooking",
            title="Cooking",
            max_duration_seconds=5,
            example_image="ZXhhbXBsZQ==",
            guide_image="Z3VpZGU=",
            user=get_mock_x_user().model_copy(update={"role": role}),
        )
    database.get_item.assert_not_awaited()
    database.put_item.assert_not_awaited()
    storage.upload_base64.assert_not_awaited()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "principal",
    [None, "", "../other", "nested/key", "   "],
)
async def test_invalid_principal_has_no_effects(principal):
    database = MockDatabase(key_names=("scenePrincipal",))
    storage = MockObjectStorage(bucket_name="test-bucket")
    with pytest.raises(ValidationError):
        await update_scene_master(
            scenes_db=database,
            storage=storage,
            bucket_name="test-bucket",
            scene_principal=principal,
            title="Cooking",
            max_duration_seconds=5,
            example_image="ZXhhbXBsZQ==",
            guide_image="Z3VpZGU=",
            user=get_mock_x_user(),
        )
    assert database.items == []
    assert storage.objects == {}


@pytest.mark.asyncio
async def test_create_and_metadata_update_preserve_durable_references():
    database = MockDatabase(key_names=("scenePrincipal",))
    storage = MockObjectStorage(bucket_name="test-bucket")
    kwargs = {
        "scenes_db": database,
        "storage": storage,
        "bucket_name": "test-bucket",
        "scene_principal": "shop_gaikan",
        "user": get_mock_x_user(),
    }
    created = await update_scene_master(
        **kwargs,
        title="Shop",
        max_duration_seconds=5,
        example_image="ZXhhbXBsZQ==",
        guide_image="Z3VpZGU=",
    )
    assert created.scene_principal == "shop_gaikan"
    assert len(storage.objects) == 2
    assert (
        await database.get_item({"scenePrincipal": "shop_gaikan"})
    ) == created.to_storage_item()
    updated = await update_scene_master(
        **kwargs,
        title="Shop exterior",
        max_duration_seconds=7,
        example_image=None,
        guide_image=None,
    )
    assert updated.title == "Shop exterior"
    assert updated.max_duration_seconds == 7
    assert updated.thumbnail_uri == created.thumbnail_uri
    assert updated.guide_uri == created.guide_uri
    assert len(storage.objects) == 2
    assert "thumbnailUrl" not in database.items[0]
    assert "guideUrl" not in database.items[0]


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "images",
    [(None, None), ("ZXhhbXBsZQ==", None), (None, "Z3VpZGU=")],
)
async def test_creation_requires_both_images_before_upload(images):
    database = MockDatabase(key_names=("scenePrincipal",))
    storage = MockObjectStorage(bucket_name="test-bucket")
    with pytest.raises(ClientUnprocessableEntityError):
        await update_scene_master(
            scenes_db=database,
            storage=storage,
            bucket_name="test-bucket",
            scene_principal="shop",
            title="Shop",
            max_duration_seconds=5,
            example_image=images[0],
            guide_image=images[1],
            user=get_mock_x_user(),
        )
    assert storage.objects == {}
    assert database.items == []


@pytest.mark.asyncio
@pytest.mark.parametrize("replacement", ["example", "guide"])
async def test_replaces_only_requested_image(replacement):
    database = MockDatabase(key_names=("scenePrincipal",))
    storage = MockObjectStorage(bucket_name="test-bucket")
    kwargs = {
        "scenes_db": database,
        "storage": storage,
        "bucket_name": "test-bucket",
        "scene_principal": "shop",
        "title": "Shop",
        "max_duration_seconds": 5,
        "user": get_mock_x_user(),
    }
    created = await update_scene_master(
        **kwargs,
        example_image="ZXhhbXBsZQ==",
        guide_image="Z3VpZGU=",
    )
    result = await update_scene_master(
        **kwargs,
        example_image="bmV3" if replacement == "example" else None,
        guide_image="bmV3" if replacement == "guide" else None,
    )
    if replacement == "example":
        assert result.thumbnail_uri != created.thumbnail_uri
        assert result.guide_uri == created.guide_uri
    else:
        assert result.guide_uri != created.guide_uri
        assert result.thumbnail_uri == created.thumbnail_uri
    assert database.items[0] == result.to_storage_item()
    assert len(storage.objects) == 2


@pytest.mark.asyncio
@pytest.mark.parametrize("failure", ["upload", "database"])
async def test_failed_write_preserves_previous_images_and_database(failure):
    database = MockDatabase(key_names=("scenePrincipal",))
    storage = MockObjectStorage(bucket_name="test-bucket")
    kwargs = {
        "scenes_db": database,
        "storage": storage,
        "bucket_name": "test-bucket",
        "scene_principal": "shop",
        "title": "Shop",
        "max_duration_seconds": 5,
        "user": get_mock_x_user(),
    }
    await update_scene_master(
        **kwargs,
        example_image="ZXhhbXBsZQ==",
        guide_image="Z3VpZGU=",
    )
    previous_objects = dict(storage.objects)
    previous_item = dict(database.items[0])
    if failure == "upload":
        upload = storage.upload_base64
        storage.upload_base64 = AsyncMock()

        async def fail_second_upload(**arguments):
            if arguments["object_key"].endswith("guide.jpg"):
                raise OSError("upload failed")
            await upload(**arguments)

        storage.upload_base64.side_effect = fail_second_upload
    else:
        database.put_item = AsyncMock(side_effect=OSError("database failed"))
    with pytest.raises(OSError, match="failed"):
        await update_scene_master(
            **kwargs,
            example_image="bmV3",
            guide_image="bmV3",
        )
    assert storage.objects == previous_objects
    assert database.items == [previous_item]


@pytest.mark.asyncio
@pytest.mark.parametrize("image", ["", "not base64", "!!!", "\u00e9"])
async def test_invalid_second_image_does_not_upload_first_image(image):
    database = MockDatabase(key_names=("scenePrincipal",))
    storage = MockObjectStorage(bucket_name="test-bucket")
    with pytest.raises(ValidationError):
        await update_scene_master(
            scenes_db=database,
            storage=storage,
            bucket_name="test-bucket",
            scene_principal="shop",
            title="Shop",
            max_duration_seconds=5,
            example_image="ZXhhbXBsZQ==",
            guide_image=image,
            user=get_mock_x_user(),
        )
    assert storage.objects == {}
    assert database.items == []
