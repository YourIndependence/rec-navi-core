# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.

"""Unit tests for the list scene masters use case."""

import pytest

from recnavi.application.master.list_scene_masters import list_scene_masters
from recnavi.core.types.scene_master import SceneMaster
from tests.mockups.mock_scene_master_repository import (
    MockSceneMasterRepository,
)


@pytest.mark.asyncio
async def test_returns_every_master():
    """The use case hands back what the repository holds."""
    masters = await list_scene_masters(
        repository=MockSceneMasterRepository(),
    )

    principals = [master.scene_principal for master in masters]
    assert principals == ["shop_gaikan", "main_dish"]


@pytest.mark.asyncio
async def test_returns_the_domain_type():
    """The application layer speaks in domain types, not in views."""
    masters = await list_scene_masters(
        repository=MockSceneMasterRepository(),
    )

    assert all(isinstance(master, SceneMaster) for master in masters)


@pytest.mark.asyncio
async def test_returns_an_empty_list_when_there_are_no_masters():
    """An empty table is not an error."""
    masters = await list_scene_masters(
        repository=MockSceneMasterRepository(masters=[]),
    )

    assert masters == []
