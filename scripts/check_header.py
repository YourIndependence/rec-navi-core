# Copyright (c) 2025 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.

"""check header"""

import re
import sys
from pathlib import Path


# Accept any year so the check does not have to be edited every January.
HEADER = re.compile(r"^# Copyright \(c\) \d{4} YourIndependence\.")

# Third-party sources carry their own headers.
EXCLUDED_DIRS = {".venv", "venv", "build", "dist", "node_modules"}

failed = []

for path in Path(".").rglob("*.py"):
    if path.name == "__init__.py":
        continue

    if EXCLUDED_DIRS & set(path.parts):
        continue

    text = path.read_text(encoding="utf-8")

    if not HEADER.match(text):
        failed.append(str(path))

if failed:
    print("Missing header:")
    for f in failed:
        print(f)
    sys.exit(1)

print("Header check passed")
