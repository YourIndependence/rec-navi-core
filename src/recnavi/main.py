# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.

"""Starting server."""

import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi import Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.errors import ServerErrorMiddleware

from recnavi.apis.cms.cms_router import cms_router
from recnavi.apis.pub.pub_router import pub_router
from recnavi.apis.root.root_router import root_router
from recnavi.config.variables import CORS_ORIGINS
from recnavi.config.variables import ENV
from recnavi.config.variables import PROJECTS_TABLE_NAME
from recnavi.config.variables import SCENES_TABLE_NAME
from recnavi.config.variables import TEMPLATES_TABLE_NAME
from recnavi.config.variables import USERS_TABLE_NAME
from recnavi.core.utils.discord_handler import post_notify_discord
from recnavi.exceptions.error_handler import custom_exception_handler
from recnavi.exceptions.error_handler import post_error_discord
from recnavi.infrastructure.database.dynamodb import DynamoDb
from recnavi.infrastructure.s3.s3_client import S3Client
from recnavi.infrastructure.ses.ses_notifier import SesNotifier


BASE_DIR = Path(__file__).resolve().parent
API_DESCRIPTION_PATH = BASE_DIR / "apis" / "api_description.md"

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Lifespan function."""
    logger.info("start booting server.")
    try:
        _app.state.database = {
            USERS_TABLE_NAME: DynamoDb(table_name=USERS_TABLE_NAME),
            PROJECTS_TABLE_NAME: DynamoDb(table_name=PROJECTS_TABLE_NAME),
            SCENES_TABLE_NAME: DynamoDb(table_name=SCENES_TABLE_NAME),
            TEMPLATES_TABLE_NAME: DynamoDb(table_name=TEMPLATES_TABLE_NAME),
        }
        logger.info("database instances initialized.")

        _app.state.notifier = SesNotifier()
        logger.info("notifier initialized.")
        _app.state.object_storage = S3Client()
        logger.info("object storage initialized.")

        if ENV not in ["LOCAL", "CI"]:
            post_notify_discord(
                title=f"{ENV}: ECS Task started!",
                message=f"{ENV}: ECS task started.",
            )
        logger.info("server initialize succeed.")
        yield

    except Exception as e:
        logger.critical("Server startup failed", exc_info=True)
        post_error_discord(
            "lifespan_startup",
            e,
            kwargs={"phase": "startup"},
        )
        raise
    finally:
        logger.info("shutdown server")


app = FastAPI(
    title="TRUST API",
    description=API_DESCRIPTION_PATH.read_text(encoding="utf-8"),
    lifespan=lifespan,
)

app.add_middleware(
    ServerErrorMiddleware,  # noqa: type
    handler=custom_exception_handler,  # noqa: type
)

app.add_middleware(
    CORSMiddleware,  # noqa: type
    allow_origins=CORS_ORIGINS,  # noqa: type
    allow_credentials=True,  # noqa: type
    allow_methods=["*"],  # noqa: type
    allow_headers=["*"],  # noqa: type
)


app.include_router(root_router)
app.include_router(cms_router)
app.include_router(pub_router)


@app.middleware("http")
async def cache_request_body(request: Request, call_next):
    """Cache request body."""
    body_bytes = await request.body()
    request.state.body = body_bytes
    response = await call_next(request)
    return response
