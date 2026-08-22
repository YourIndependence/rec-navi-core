# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.


"""UserTableItem tests"""

import pytest
from pydantic import ValidationError

from recnavi.core.types.user_table_item import UserRole
from recnavi.core.types.user_table_item import UserTableItem


ITEM = {
    "userId": "user_tanaka",
    "groupId": "group_acme",
    "userName": "Tanaka",
    "role": "owner",
}


def test_roles():
    assert [role.value for role in UserRole] == ["admin", "owner", "staff"]


def test_load_from_table_item():
    user = UserTableItem.model_validate(ITEM)

    assert user.user_id == "user_tanaka"
    assert user.group_id == "group_acme"
    assert user.role is UserRole.OWNER


def test_dump_to_table_item():
    user = UserTableItem.model_validate(ITEM)

    assert user.model_dump(by_alias=True, mode="json") == ITEM


def test_reject_unknown_role():
    with pytest.raises(ValidationError):
        UserTableItem.model_validate({**ITEM, "role": "bogus"})
