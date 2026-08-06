# Copyright (c) 2025 YourIndependence. All rights reserved.
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
ENV = os.environ.get(
    "ENV", "LOCAL"
)  # main, staging, dev, LOCAL, LOCAL_CONTAINER, CI
REGION = "ap-northeast-1"

COGNITO_CLIENT_ID = os.environ.get("COGNITO_CLIENT_ID", "dummy")
COGNITO_USER_POOL_ID = os.environ.get("COGNITO_USER_POOL_ID", "dummy")

LOG_BUCKET_NAME = os.environ.get("LOG_BUCKET_NAME", "recnavi-dev-log-data")
