# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.

"""Root router"""

import time

from fastapi import APIRouter

from recnavi.config.variables import ENV


root_router = APIRouter(tags=["Root"])


@root_router.get("/health")
def health_check():
    """Health check api."""
    return {"status": "ok"}


@root_router.get("/greeting")
async def greeting():
    """Test API endpoint **without** authentication."""
    return {
        "status": "ok",
        "timestamp": int(time.time()),
        "environment": ENV,
    }
