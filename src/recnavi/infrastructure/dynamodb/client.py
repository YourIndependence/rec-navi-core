# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.


"""DynamoDB client."""

import boto3

from recnavi.config.variables import REGION


def get_table(table_name: str):
    """Get a handle on one DynamoDB table."""
    resource = boto3.resource("dynamodb", region_name=REGION)
    return resource.Table(table_name)
