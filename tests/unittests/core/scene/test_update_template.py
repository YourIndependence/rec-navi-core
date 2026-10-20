# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or reproduction of this software is strictly prohibited.
#
# For internal use only.
# developer team.

"""Template update contracts."""

from unittest.mock import AsyncMock

import pytest

from recnavi.core.scene.update_template import update_template
from recnavi.core.types.user import UserRole
from recnavi.exceptions.exceptions import ClientAuthorizationError
from recnavi.exceptions.exceptions import ClientValueError
from tests.mockups.mock_database import MockDatabase
from tests.mockups.mock_object_storage import MockObjectStorage
from tests.mockups.mock_users import get_mock_x_user


@pytest.fixture
def dependencies():
    """Provide isolated domain collaborators."""
    return {
        "templates_db": MockDatabase(key_names=("templateId",)),
        "scenes_db": MockDatabase(
            initial_items=[{"scenePrincipal": "cooking"}],
        ),
        "storage": MockObjectStorage(bucket_name="test-bucket"),
        "user": get_mock_x_user().model_copy(update={"role": UserRole.ADMIN}),
    }


@pytest.mark.asyncio
async def test_current_storage_contract_and_durable_thumbnail(dependencies):
    template = await update_template(
        **dependencies,
        template_id="regression",
        title="Regression",
        scene_principals=["cooking", "cooking"],
        thumbnail_image="bmV3",
    )
    stored = await dependencies["templates_db"].get_item(
        {"templateId": "regression"},
    )
    assert stored["thumbnailUri"] == template.thumbnail_uri
    assert "thumbnailUrl" not in stored
    assert stored["scenePrincipals"] == ["cooking", "cooking"]
    assert dependencies["storage"].objects[
        ("test-bucket", template.thumbnail_uri)
    ] == (b"new", "image/jpeg")
    updated = await update_template(
        **dependencies,
        template_id="regression",
        title="Renamed",
    )
    assert updated.thumbnail_uri == template.thumbnail_uri
    assert updated.scene_principals == template.scene_principals
    assert updated.title == "Renamed"


@pytest.mark.asyncio
@pytest.mark.parametrize("role", [UserRole.OWNER, UserRole.STAFF])
async def test_non_admin_denied_before_io(dependencies, role):
    dependencies["user"] = get_mock_x_user().model_copy(update={"role": role})
    database = AsyncMock()
    dependencies["templates_db"] = database
    with pytest.raises(ClientAuthorizationError):
        await update_template(**dependencies, template_id="denied")
    database.get_item.assert_not_awaited()
    assert dependencies["storage"].objects == {}


@pytest.mark.asyncio
async def test_unknown_principal_has_no_effects(dependencies):
    with pytest.raises(ClientValueError, match="Unknown scenePrincipals"):
        await update_template(
            **dependencies,
            template_id="unknown",
            title="Unknown",
            scene_principals=["missing"],
            thumbnail_image="bmV3",
        )
    assert dependencies["storage"].objects == {}
    assert (await dependencies["templates_db"].scan()).items == []


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "missing",
    ["title", "scene_principals", "thumbnail_image"],
)
async def test_create_requires_metadata_and_image(dependencies, missing):
    payload = {
        "title": "New",
        "scene_principals": [],
        "thumbnail_image": "bmV3",
    }
    payload.pop(missing)
    with pytest.raises(ClientValueError):
        await update_template(**dependencies, template_id="new", **payload)
    assert dependencies["storage"].objects == {}


@pytest.mark.asyncio
async def test_failed_save_preserves_old_image_and_removes_new_image(
    dependencies,
):
    template = await update_template(
        **dependencies,
        template_id="failure",
        title="Existing",
        scene_principals=[],
        thumbnail_image="b2xk",
    )
    before = dependencies["storage"].objects.copy()
    dependencies["templates_db"].put_item = AsyncMock(
        side_effect=RuntimeError("database unavailable"),
    )
    with pytest.raises(RuntimeError, match="database unavailable"):
        await update_template(
            **dependencies,
            template_id="failure",
            thumbnail_image="bmV3",
        )
    assert dependencies["storage"].objects == before
    stored = await dependencies["templates_db"].get_item(
        {"templateId": "failure"},
    )
    assert stored["thumbnailUri"] == template.thumbnail_uri


@pytest.mark.asyncio
async def test_replacement_deletes_only_previous_thumbnail(dependencies):
    template = await update_template(
        **dependencies,
        template_id="replacement",
        title="Existing",
        scene_principals=[],
        thumbnail_image="b2xk",
    )
    previous = template.thumbnail_uri
    updated = await update_template(
        **dependencies,
        template_id="replacement",
        thumbnail_image="bmV3",
    )
    assert updated.thumbnail_uri != previous
    assert ("test-bucket", previous) not in dependencies["storage"].objects
    assert len(dependencies["storage"].objects) == 1
