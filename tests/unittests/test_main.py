# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.

from unittest.mock import patch

import pytest
from fastapi import FastAPI

from recnavi import main


@pytest.mark.asyncio
async def test_lifespan_injects_database_and_object_storage():
    app = FastAPI()
    database_instances = [object() for _ in range(4)]
    object_storage = object()

    with (
        patch.object(main, "ENV", "CI"),
        patch.object(
            main,
            "DynamoDb",
            side_effect=database_instances,
        ) as dynamo_db,
        patch.object(
            main,
            "S3Client",
            return_value=object_storage,
        ) as s3_client,
    ):
        async with main.lifespan(app):
            assert app.state.database == {
                main.USERS_TABLE_NAME: database_instances[0],
                main.PROJECTS_TABLE_NAME: database_instances[1],
                main.SCENES_TABLE_NAME: database_instances[2],
                main.TEMPLATES_TABLE_NAME: database_instances[3],
            }
            assert app.state.object_storage is object_storage

    assert dynamo_db.call_args_list == [
        ((), {"table_name": main.USERS_TABLE_NAME}),
        ((), {"table_name": main.PROJECTS_TABLE_NAME}),
        ((), {"table_name": main.SCENES_TABLE_NAME}),
        ((), {"table_name": main.TEMPLATES_TABLE_NAME}),
    ]
    s3_client.assert_called_once_with(bucket_name=main.MEDIA_BUCKET_NAME)
