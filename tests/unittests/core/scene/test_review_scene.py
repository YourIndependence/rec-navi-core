# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.

"""Tests for review_scene core function."""

from unittest.mock import AsyncMock

import pytest

from recnavi.core.project.scene_urls import SCENE_URL_EXPIRATION_SECONDS
from recnavi.core.scene.review_scene import review_scene
from recnavi.core.types.project import Project
from recnavi.core.types.project import ProjectStatus
from recnavi.core.types.scene import ReviewSceneResult
from recnavi.core.types.scene import Scene
from recnavi.core.types.scene import SceneStatus
from recnavi.core.types.user import User
from recnavi.core.types.user import UserRole
from recnavi.exceptions.exceptions import ClientAuthorizationError
from recnavi.exceptions.exceptions import ClientConflictError
from recnavi.exceptions.exceptions import ClientNotFoundError
from tests.mockups.mock_database import MockDatabase
from tests.mockups.mock_object_storage import MockObjectStorage


@pytest.mark.asyncio
async def test_review_scene_approved_returns_correct_data():
    """Test review_scene updates project with APPROVED status."""
    project = Project(
        project_id="proj-123",
        group_id="group-1",
        owner_user_id="owner-1",
        project_name="Test Project",
        scenes=[
            Scene(
                scene_id="scene-456",
                scene_principal="cooking",
                status=SceneStatus.PENDING,
            ),
        ],
        created_at="2026-01-01T00:00:00Z",
        updated_at="2026-01-01T00:00:00Z",
    )
    db = MockDatabase(initial_items=[project.model_dump(by_alias=True)])
    user = User(
        user_id="owner-1",
        user_name="Test Owner",
        group_id="group-1",
        role=UserRole.OWNER,
    )

    result_project = await review_scene(
        projects_db=db,
        project_id="proj-123",
        scene_id="scene-456",
        result=ReviewSceneResult.APPROVED,
        review_comment=None,
        user=user,
        storage=MockObjectStorage(bucket_name="bucket"),
    )

    assert result_project.project_id == "proj-123"
    assert result_project.scenes[0].status == SceneStatus.APPROVED
    assert (
        result_project.model_dump(mode="json")["scenes"][0]["status"]
        == "approved"
    )


@pytest.mark.asyncio
async def test_review_scene_rejected_returns_correct_data():
    """Test review_scene updates project with REJECTED status."""
    project = Project(
        project_id="proj-123",
        group_id="group-1",
        owner_user_id="owner-1",
        project_name="Test Project",
        scenes=[
            Scene(
                scene_id="scene-456",
                scene_principal="cooking",
                status=SceneStatus.APPROVED,
            ),
        ],
        created_at="2026-01-01T00:00:00Z",
        updated_at="2026-01-01T00:00:00Z",
    )
    db = MockDatabase(initial_items=[project.model_dump(by_alias=True)])
    user = User(
        user_id="owner-1",
        user_name="Test Owner",
        group_id="group-1",
        role=UserRole.OWNER,
    )

    result_project = await review_scene(
        projects_db=db,
        project_id="proj-123",
        scene_id="scene-456",
        result=ReviewSceneResult.REJECTED,
        review_comment=None,
        user=user,
        storage=MockObjectStorage(bucket_name="bucket"),
    )

    assert result_project.project_id == "proj-123"
    assert result_project.scenes[0].status == SceneStatus.REJECTED


@pytest.mark.asyncio
async def test_review_scene_raises_403_for_non_owner():
    """Test review_scene raises 403 for non-owner user."""
    project = Project(
        project_id="proj-123",
        group_id="group-1",
        owner_user_id="owner-1",
        project_name="Test Project",
        scenes=[
            Scene(
                scene_id="scene-456",
                scene_principal="cooking",
                status=SceneStatus.PENDING,
            ),
        ],
        created_at="2026-01-01T00:00:00Z",
        updated_at="2026-01-01T00:00:00Z",
    )
    db = MockDatabase(initial_items=[project.model_dump(by_alias=True)])
    staff_user = User(
        user_id="staff-1",
        user_name="Test Staff",
        group_id="group-1",
        role=UserRole.STAFF,
    )

    with pytest.raises(ClientAuthorizationError):
        await review_scene(
            projects_db=db,
            project_id="proj-123",
            scene_id="scene-456",
            result=ReviewSceneResult.APPROVED,
            review_comment=None,
            user=staff_user,
            storage=MockObjectStorage(bucket_name="bucket"),
        )


@pytest.mark.asyncio
async def test_review_scene_raises_403_for_wrong_group():
    """Test review_scene raises 403 for different group."""
    project = Project(
        project_id="proj-123",
        group_id="group-1",
        owner_user_id="owner-1",
        project_name="Test Project",
        scenes=[
            Scene(
                scene_id="scene-456",
                scene_principal="cooking",
                status=SceneStatus.PENDING,
            ),
        ],
        created_at="2026-01-01T00:00:00Z",
        updated_at="2026-01-01T00:00:00Z",
    )
    db = MockDatabase(initial_items=[project.model_dump(by_alias=True)])
    other_owner = User(
        user_id="owner-2",
        user_name="Other Owner",
        group_id="group-2",
        role=UserRole.OWNER,
    )

    with pytest.raises(ClientAuthorizationError):
        await review_scene(
            projects_db=db,
            project_id="proj-123",
            scene_id="scene-456",
            result=ReviewSceneResult.APPROVED,
            review_comment=None,
            user=other_owner,
            storage=MockObjectStorage(bucket_name="bucket"),
        )


@pytest.mark.asyncio
async def test_review_scene_raises_404_when_scene_not_found():
    """Test review_scene raises 404 when scene not found."""
    project = Project(
        project_id="proj-123",
        group_id="group-1",
        owner_user_id="owner-1",
        project_name="Test Project",
        scenes=[
            Scene(
                scene_id="scene-456",
                scene_principal="cooking",
                status=SceneStatus.PENDING,
            ),
        ],
        created_at="2026-01-01T00:00:00Z",
        updated_at="2026-01-01T00:00:00Z",
    )
    db = MockDatabase(initial_items=[project.model_dump(by_alias=True)])
    user = User(
        user_id="owner-1",
        user_name="Test Owner",
        group_id="group-1",
        role=UserRole.OWNER,
    )

    with pytest.raises(ClientNotFoundError):
        await review_scene(
            projects_db=db,
            project_id="proj-123",
            scene_id="nonexistent-scene",
            result=ReviewSceneResult.APPROVED,
            review_comment=None,
            user=user,
            storage=MockObjectStorage(bucket_name="bucket"),
        )


@pytest.mark.asyncio
async def test_review_scene_allows_re_review():
    """Test review_scene allows changing APPROVED to REJECTED."""
    project = Project(
        project_id="proj-123",
        group_id="group-1",
        owner_user_id="owner-1",
        project_name="Test Project",
        scenes=[
            Scene(
                scene_id="scene-456",
                scene_principal="cooking",
                status=SceneStatus.APPROVED,
            ),
        ],
        created_at="2026-01-01T00:00:00Z",
        updated_at="2026-01-01T00:00:00Z",
    )
    db = MockDatabase(initial_items=[project.model_dump(by_alias=True)])
    user = User(
        user_id="owner-1",
        user_name="Test Owner",
        group_id="group-1",
        role=UserRole.OWNER,
    )

    result_project = await review_scene(
        projects_db=db,
        project_id="proj-123",
        scene_id="scene-456",
        result=ReviewSceneResult.REJECTED,
        review_comment=None,
        user=user,
        storage=MockObjectStorage(bucket_name="bucket"),
    )

    assert result_project.scenes[0].status == SceneStatus.REJECTED
    assert result_project.scenes[0].scene_id == "scene-456"


@pytest.mark.asyncio
async def test_review_scene_returns_view_with_urls_and_no_keys():
    """Test review_scene returns presigned URLs and hides storage keys."""
    project = Project(
        project_id="proj-123",
        group_id="group-1",
        owner_user_id="owner-1",
        project_name="Test Project",
        scenes=[
            Scene(
                scene_id="scene-456",
                scene_principal="cooking",
                status=SceneStatus.PENDING,
                video_key="videos/s456.mp4",
                thumbnail_key="thumbnails/s456.jpg",
            ),
            Scene(
                scene_id="scene-789",
                scene_principal="serving",
                status=SceneStatus.PENDING,
            ),
        ],
        created_at="2026-01-01T00:00:00Z",
        updated_at="2026-01-01T00:00:00Z",
    )
    db = MockDatabase(initial_items=[project.model_dump(by_alias=True)])
    user = User(
        user_id="owner-1",
        user_name="Test Owner",
        group_id="group-1",
        role=UserRole.OWNER,
    )

    view = await review_scene(
        projects_db=db,
        project_id="proj-123",
        scene_id="scene-456",
        result=ReviewSceneResult.APPROVED,
        review_comment=None,
        user=user,
        storage=MockObjectStorage(bucket_name="bucket"),
    )

    expires = SCENE_URL_EXPIRATION_SECONDS
    assert view.scenes[0].status == SceneStatus.APPROVED
    assert view.scenes[0].video_url == (
        f"mock://bucket/videos/s456.mp4?expires={expires}"
    )
    assert view.scenes[0].thumbnail_url == (
        f"mock://bucket/thumbnails/s456.jpg?expires={expires}"
    )
    assert view.scenes[1].video_url is None
    assert view.scenes[1].thumbnail_url is None
    dumped = view.model_dump(by_alias=True)["scenes"][0]
    assert "videoKey" not in dumped
    assert "thumbnailKey" not in dumped


@pytest.mark.asyncio
async def test_review_scene_rejected_moves_submitted_project_to_in_progress():
    """Test rejecting a scene reopens a SUBMITTED project."""
    project = Project(
        project_id="proj-123",
        group_id="group-1",
        owner_user_id="owner-1",
        project_name="Test Project",
        status=ProjectStatus.SUBMITTED,
        scenes=[
            Scene(
                scene_id="scene-456",
                scene_principal="cooking",
                status=SceneStatus.APPROVED,
            ),
        ],
        created_at="2026-01-01T00:00:00Z",
        updated_at="2026-01-01T00:00:00Z",
    )
    db = MockDatabase(initial_items=[project.model_dump(by_alias=True)])
    user = User(
        user_id="owner-1",
        user_name="Test Owner",
        group_id="group-1",
        role=UserRole.OWNER,
    )

    view = await review_scene(
        projects_db=db,
        project_id="proj-123",
        scene_id="scene-456",
        result=ReviewSceneResult.REJECTED,
        review_comment="Please re-record",
        user=user,
        storage=MockObjectStorage(bucket_name="bucket"),
    )

    assert view.status == ProjectStatus.IN_PROGRESS


@pytest.mark.asyncio
async def test_review_scene_approved_keeps_submitted_project_submitted():
    """Test approving a scene does not change the project status."""
    project = Project(
        project_id="proj-123",
        group_id="group-1",
        owner_user_id="owner-1",
        project_name="Test Project",
        status=ProjectStatus.SUBMITTED,
        scenes=[
            Scene(
                scene_id="scene-456",
                scene_principal="cooking",
                status=SceneStatus.PENDING,
                video_key="videos/scene-456.mp4",
            ),
        ],
        created_at="2026-01-01T00:00:00Z",
        updated_at="2026-01-01T00:00:00Z",
    )
    db = MockDatabase(initial_items=[project.model_dump(by_alias=True)])
    user = User(
        user_id="owner-1",
        user_name="Test Owner",
        group_id="group-1",
        role=UserRole.OWNER,
    )

    view = await review_scene(
        projects_db=db,
        project_id="proj-123",
        scene_id="scene-456",
        result=ReviewSceneResult.APPROVED,
        review_comment=None,
        user=user,
        storage=MockObjectStorage(bucket_name="bucket"),
    )

    assert view.status == ProjectStatus.SUBMITTED
    assert view.scenes[0].status == SceneStatus.APPROVED


@pytest.mark.asyncio
@pytest.mark.parametrize("legacy", [False, True])
async def test_review_advances_version_and_clears_previous_comment(
    legacy: bool,
):
    """Review participates in project locking and replaces prior review data."""
    project = Project(
        project_id="p",
        project_name="P",
        owner_user_id="owner",
        group_id="g",
        created_at="2026-01-01T00:00:00Z",
        version=4,
        scenes=[
            Scene(
                scene_id="s",
                scene_principal="cooking",
                status=SceneStatus.REJECTED,
                review_comment="Old comment",
            ),
        ],
    )
    item = project.model_dump(by_alias=True)
    if legacy:
        item.pop("version")
    db = MockDatabase([item])
    result = await review_scene(
        projects_db=db,
        project_id="p",
        scene_id="s",
        result=ReviewSceneResult.APPROVED,
        review_comment=None,
        user=User(
            user_id="owner",
            user_name="Owner",
            group_id="g",
            role=UserRole.OWNER,
        ),
        storage=MockObjectStorage(bucket_name="bucket"),
    )
    saved = await db.get_item({"projectId": "p"})
    assert saved["version"] == (1 if legacy else 5)
    assert saved["updatedAt"] is not None
    assert saved["scenes"][0]["reviewComment"] is None
    assert saved["scenes"][0]["reviewedBy"] == "owner"
    assert result.scenes[0].reviewed_at is not None


@pytest.mark.asyncio
async def test_review_propagates_concurrent_write_conflict():
    """A concurrent recording or project update cannot be overwritten."""
    project = Project(
        project_id="p",
        project_name="P",
        owner_user_id="owner",
        group_id="g",
        created_at="2026-01-01T00:00:00Z",
        version=4,
        scenes=[Scene(scene_id="s", scene_principal="cooking")],
    )
    db = AsyncMock()
    db.get_item.return_value = project.model_dump(by_alias=True)
    db.put_item.side_effect = ClientConflictError("Concurrent write")
    with pytest.raises(ClientConflictError):
        await review_scene(
            projects_db=db,
            project_id="p",
            scene_id="s",
            result=ReviewSceneResult.APPROVED,
            review_comment=None,
            user=User(
                user_id="owner",
                user_name="Owner",
                group_id="g",
                role=UserRole.OWNER,
            ),
            storage=MockObjectStorage(bucket_name="bucket"),
        )
    assert db.put_item.call_args.kwargs["expression_attribute_values"] == {
        ":previous_version": 4,
    }


@pytest.mark.asyncio
async def test_review_denies_another_owner_in_same_group():
    """Group membership alone does not grant project owner permissions."""
    project = Project(
        project_id="p",
        project_name="P",
        owner_user_id="owner",
        group_id="g",
        created_at="2026-01-01T00:00:00Z",
        scenes=[Scene(scene_id="s", scene_principal="cooking")],
    )
    with pytest.raises(ClientAuthorizationError):
        await review_scene(
            projects_db=MockDatabase([project.model_dump(by_alias=True)]),
            project_id="p",
            scene_id="s",
            result=ReviewSceneResult.APPROVED,
            review_comment=None,
            user=User(
                user_id="other",
                user_name="Other",
                group_id="g",
                role=UserRole.OWNER,
            ),
            storage=MockObjectStorage(bucket_name="bucket"),
        )
