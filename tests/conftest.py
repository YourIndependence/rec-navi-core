# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.

"""Pytest configuration for unit tests."""

import sys
from pathlib import Path


# Add tests directory to Python path for importing test mockups
tests_dir = Path(__file__).parent
sys.path.insert(0, str(tests_dir))
