# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or reproduction of this software is strictly prohibited.
#
# For internal use only.
# developer team.

"""Unit tests for exceptions."""

from recnavi.exceptions.exceptions import BaseClientExceptionError
from recnavi.exceptions.exceptions import ClientConflictError


def test_client_conflict_error_is_base_client_exception():
    """Test ClientConflictError inherits from BaseClientExceptionError."""
    error = ClientConflictError("version mismatch")
    assert isinstance(error, BaseClientExceptionError)
    assert str(error) == "version mismatch"
