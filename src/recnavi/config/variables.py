# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.

"""application global variables."""

import os


# general
# main, staging, dev, LOCAL, LOCAL_CONTAINER, CI
ENV = os.environ.get("ENV", "LOCAL")
REGION = "ap-northeast-1"

COGNITO_CLIENT_ID = os.environ.get("COGNITO_CLIENT_ID", "dummy")
COGNITO_USER_POOL_ID = os.environ.get("COGNITO_USER_POOL_ID", "dummy")

USERS_TABLE_NAME = os.environ.get("DDB_USERS_TABLE", "rec-navi-dev-users")
PROJECTS_TABLE_NAME = os.environ.get(
    "DDB_PROJECTS_TABLE",
    "rec-navi-dev-projects",
)
SCENES_TABLE_NAME = os.environ.get("DDB_SCENES_TABLE", "rec-navi-dev-scenes")
TEMPLATES_TABLE_NAME = os.environ.get(
    "DDB_SCENE_TEMPLATES_TABLE",
    "rec-navi-dev-scene-templates",
)

MEDIA_BUCKET_NAME = os.environ.get(
    "MEDIA_BUCKET_NAME",
    "rec-navi-dev-media",
)

APP_DOMAINS = "rec-navi.com"


def _get_cors_origins() -> list[str]:
    origins = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]
    origins.extend(f"https://{ENV}.{domain}" for domain in APP_DOMAINS)
    if ENV == "main":
        origins.extend(f"https://service.{domain}" for domain in APP_DOMAINS)
    return origins


CORS_ORIGINS = _get_cors_origins()

LOG_BUCKET_NAME = os.environ.get("LOG_BUCKET_NAME", "rec-navi-dev-log-data")
