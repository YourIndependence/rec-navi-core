# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.


"""User tests"""

import pytest
from pydantic import ValidationError

from recnavi.core.types.user import User
from recnavi.core.types.user import UserRole


USER = {
    "userId": "user_tanaka",
    "groupId": "group_acme",
    "userName": "Tanaka",
    "role": "owner",
}


def test_roles():
    assert [role.value for role in UserRole] == ["admin", "owner", "staff"]


def test_load():
    user = User.model_validate(USER)

    assert user.user_id == "user_tanaka"
    assert user.group_id == "group_acme"
    assert user.role is UserRole.OWNER


def test_dump_keeps_camel_case():
    user = User.model_validate(USER)

    assert user.model_dump(by_alias=True, mode="json") == USER


def test_reject_unknown_role():
    with pytest.raises(ValidationError):
        User.model_validate({**USER, "role": "bogus"})
