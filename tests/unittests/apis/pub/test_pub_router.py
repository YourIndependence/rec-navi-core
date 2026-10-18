# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.

"""Public scene image HTTP parsing and use-case delegation."""

from unittest.mock import AsyncMock
from unittest.mock import patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from recnavi.apis.pub.pub_router import pub_router
from recnavi.config.variables import SCENES_TABLE_NAME


@pytest.mark.parametrize(
    ("kind", "mime"),
    [("example", "image/jpeg"), ("guide", "image/png")],
)
def test_public_image_uses_dedicated_storage_without_auth(kind, mime):
    app = FastAPI()
    app.include_router(pub_router)
    scenes_db = object()
    storage = object()
    app.state.database = {SCENES_TABLE_NAME: scenes_db}
    app.state.scene_images_storage = storage
    with patch(
        "recnavi.apis.pub.pub_router.get_scene_thumbnail_usecase",
        new=AsyncMock(return_value=(b"image", mime)),
    ) as usecase:
        with TestClient(app) as client:
            response = client.get(
                "/getSceneThumbnail",
                params={"scenePrincipal": "cooking", "kind": kind},
            )
    assert response.status_code == 200
    assert response.content == b"image"
    assert response.headers["content-type"] == mime
    assert response.headers["cache-control"] == "public, max-age=86400"
    usecase.assert_awaited_once_with(
        scenes_db=scenes_db,
        scene_principal="cooking",
        kind=kind,
        storage=storage,
    )
