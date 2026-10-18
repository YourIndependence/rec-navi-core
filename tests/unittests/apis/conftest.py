# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.

"""Configuration and shared context for API tests.
Detected automatically by pytest, so no need to import it in the test code.
"""

from collections.abc import Iterator

import pytest
from fastapi import APIRouter
from fastapi import FastAPI
from fastapi.testclient import TestClient

from recnavi.apis.auth.auth import verify_user
from recnavi.apis.cms.cms_router import cms_router
from recnavi.apis.root.root_router import root_router
from recnavi.apis.staff.staff_router import staff_router
from recnavi.config.variables import PROJECTS_TABLE_NAME
from recnavi.config.variables import SCENES_TABLE_NAME
from recnavi.config.variables import TEMPLATES_TABLE_NAME
from recnavi.config.variables import USERS_TABLE_NAME
from tests.mockups.mock_database import MockDatabase
from tests.mockups.mock_object_storage import MockObjectStorage
from tests.mockups.mock_users import get_mock_x_user


def _client_for_router(router: APIRouter) -> Iterator[TestClient]:
    """Exercise one real router without production startup or shared state."""
    api_app = FastAPI()
    api_app.include_router(router)
    api_app.dependency_overrides[verify_user] = get_mock_x_user
    api_app.state.database = {
        USERS_TABLE_NAME: MockDatabase(),
        PROJECTS_TABLE_NAME: MockDatabase(),
        SCENES_TABLE_NAME: MockDatabase(),
        TEMPLATES_TABLE_NAME: MockDatabase(),
    }
    api_app.state.object_storage = MockObjectStorage(bucket_name="unit-media")
    with TestClient(api_app) as test_client:
        yield test_client


@pytest.fixture(scope="module")
def cms_client() -> Iterator[TestClient]:
    yield from _client_for_router(cms_router)


@pytest.fixture(scope="module")
def staff_client() -> Iterator[TestClient]:
    yield from _client_for_router(staff_router)


@pytest.fixture(scope="module")
def root_client() -> Iterator[TestClient]:
    yield from _client_for_router(root_router)


@pytest.fixture(scope="session")
def auth_headers():
    """Standard authentication headers for API requests"""
    dummy_token = "dummy_token"
    return {
        "Authorization": f"Bearer {dummy_token}",
    }
