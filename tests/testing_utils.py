# Copyright (c) 2025 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.

"""test utils"""

from __future__ import annotations

import random
import string
from typing import TYPE_CHECKING


if TYPE_CHECKING:
    pass


def get_random_string(k=1):
    """Get random string"""
    return "".join(random.choices(string.ascii_letters + string.digits, k=k))
