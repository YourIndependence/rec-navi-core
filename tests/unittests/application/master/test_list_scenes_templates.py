# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.

"""Unit tests for the list scenes templates use case."""

import pytest

from recnavi.application.master.list_scenes_templates import (
    list_scenes_templates,
)
from recnavi.core.types.scenes_template import ScenesTemplate
from tests.mockups.mock_scenes_template_repository import (
    MockScenesTemplateRepository,
)


@pytest.mark.asyncio
async def test_returns_every_template():
    """The use case hands back what the repository holds."""
    templates = await list_scenes_templates(
        repository=MockScenesTemplateRepository(),
    )

    assert [t.template_id for t in templates] == ["tpl_cafe", "tpl_hotel"]


@pytest.mark.asyncio
async def test_returns_the_domain_type():
    """The application layer speaks in domain types, not in views."""
    templates = await list_scenes_templates(
        repository=MockScenesTemplateRepository(),
    )

    assert all(isinstance(t, ScenesTemplate) for t in templates)


@pytest.mark.asyncio
async def test_returns_an_empty_list_when_there_are_none():
    """An empty table is not an error."""
    templates = await list_scenes_templates(
        repository=MockScenesTemplateRepository(templates=[]),
    )

    assert templates == []
