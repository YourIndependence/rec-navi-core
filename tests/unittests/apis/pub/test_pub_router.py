# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.

"""Public template image transport and dependency selection."""

from unittest.mock import AsyncMock
from unittest.mock import patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from recnavi.apis.pub.pub_router import pub_router
from recnavi.config.variables import TEMPLATES_TABLE_NAME


@pytest.mark.parametrize("mime", ["image/jpeg", "image/png"])
def test_template_thumbnail_is_public_and_uses_image_storage(mime):
    app = FastAPI()
    app.include_router(pub_router)
    database = object()
    storage = object()
    app.state.database = {TEMPLATES_TABLE_NAME: database}
    app.state.scene_images_storage = storage
    with patch(
        "recnavi.apis.pub.pub_router.get_template_thumbnail_usecase",
        new=AsyncMock(return_value=(b"image", mime)),
    ) as usecase:
        with TestClient(app) as client:
            response = client.get(
                "/getTemplateThumbnail",
                params={"templateId": "cafe"},
            )
    assert response.status_code == 200
    assert response.content == b"image"
    assert response.headers["content-type"] == mime
    assert response.headers["cache-control"] == "public, max-age=86400"
    usecase.assert_awaited_once_with(
        templates_db=database,
        template_id="cafe",
        storage=storage,
    )
