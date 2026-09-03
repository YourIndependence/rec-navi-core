# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.


"""S3 client."""

import boto3

from recnavi.config.variables import REGION


def get_client():
    """Get an S3 client."""
    return boto3.client("s3", region_name=REGION)
