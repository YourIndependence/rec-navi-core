# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.

"""Integration tests for the OpenAPI document."""


def test_openapi_operation_ids_are_unique(client):
    """Every route yields a distinct operationId."""
    response = client.get("/openapi.json")
    assert response.status_code == 200
    schema = response.json()
    operation_ids = [
        operation["operationId"]
        for path_item in schema["paths"].values()
        for operation in path_item.values()
    ]

    assert len(operation_ids) == len(set(operation_ids))


def test_openapi_has_get_my_projects_and_single_get_projects(client):
    """Both list endpoints exist exactly once."""
    response = client.get("/openapi.json")
    assert response.status_code == 200
    paths = response.json()["paths"]

    assert "get" in paths["/getMyProjects"]
    assert "get" in paths["/getProjects"]
