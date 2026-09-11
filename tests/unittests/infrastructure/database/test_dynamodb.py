# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.

"""Tests for DynamoDb Decimal conversion logic."""

from decimal import Decimal

from recnavi.infrastructure.database.dynamodb import (
    _convert_from_dynamodb_format,
)
from recnavi.infrastructure.database.dynamodb import (
    _convert_to_dynamodb_format,
)


def test_convert_to_dynamodb_converts_int_to_decimal():
    """Test _convert_to_dynamodb_format converts int to Decimal."""
    item = {"userId": "user-123", "age": 25, "score": 100}

    result = _convert_to_dynamodb_format(item)

    assert result["userId"] == "user-123"
    assert isinstance(result["age"], Decimal)
    assert isinstance(result["score"], Decimal)
    assert result["age"] == Decimal("25")
    assert result["score"] == Decimal("100")


def test_convert_to_dynamodb_converts_float_to_decimal():
    """Test _convert_to_dynamodb_format converts float to Decimal."""
    item = {"userId": "user-123", "rating": 4.5, "price": 19.99}

    result = _convert_to_dynamodb_format(item)

    assert result["userId"] == "user-123"
    assert isinstance(result["rating"], Decimal)
    assert isinstance(result["price"], Decimal)
    assert float(result["rating"]) == 4.5
    assert float(result["price"]) == 19.99


def test_convert_to_dynamodb_preserves_strings():
    """Test _convert_to_dynamodb_format preserves string values."""
    item = {"userId": "user-123", "userName": "Test User"}

    result = _convert_to_dynamodb_format(item)

    assert result["userId"] == "user-123"
    assert result["userName"] == "Test User"


def test_convert_to_dynamodb_preserves_booleans():
    """Test _convert_to_dynamodb_format preserves boolean values."""
    item = {"userId": "user-123", "isActive": True, "isDeleted": False}

    result = _convert_to_dynamodb_format(item)

    assert result["isActive"] is True
    assert result["isDeleted"] is False


def test_convert_to_dynamodb_handles_nested_dicts():
    """Test _convert_to_dynamodb_format handles nested dictionaries."""
    item = {
        "userId": "user-123",
        "profile": {"age": 30, "rating": 4.5, "name": "Alice"},
    }

    result = _convert_to_dynamodb_format(item)

    assert result["userId"] == "user-123"
    assert isinstance(result["profile"]["age"], Decimal)
    assert isinstance(result["profile"]["rating"], Decimal)
    assert result["profile"]["name"] == "Alice"


def test_convert_to_dynamodb_handles_lists():
    """Test _convert_to_dynamodb_format handles lists."""
    item = {
        "userId": "user-123",
        "scores": [10, 20, 30],
        "ratings": [4.5, 3.8],
    }

    result = _convert_to_dynamodb_format(item)

    assert result["userId"] == "user-123"
    assert all(isinstance(score, Decimal) for score in result["scores"])
    assert all(isinstance(rating, Decimal) for rating in result["ratings"])


def test_convert_from_dynamodb_converts_decimal_to_int():
    """Test _convert_from_dynamodb_format converts Decimal to int."""
    item = {
        "userId": "user-123",
        "age": Decimal("25"),
        "score": Decimal("100"),
    }

    result = _convert_from_dynamodb_format(item)

    assert result["userId"] == "user-123"
    assert isinstance(result["age"], int)
    assert isinstance(result["score"], int)
    assert result["age"] == 25
    assert result["score"] == 100


def test_convert_from_dynamodb_converts_decimal_to_float():
    """Test _convert_from_dynamodb_format converts Decimal to float."""
    item = {
        "userId": "user-123",
        "rating": Decimal("4.5"),
        "price": Decimal("19.99"),
    }

    result = _convert_from_dynamodb_format(item)

    assert result["userId"] == "user-123"
    assert isinstance(result["rating"], float)
    assert isinstance(result["price"], float)
    assert result["rating"] == 4.5
    assert result["price"] == 19.99


def test_convert_from_dynamodb_preserves_strings():
    """Test _convert_from_dynamodb_format preserves string values."""
    item = {"userId": "user-123", "userName": "Test User"}

    result = _convert_from_dynamodb_format(item)

    assert result["userId"] == "user-123"
    assert result["userName"] == "Test User"


def test_convert_from_dynamodb_handles_nested_dicts():
    """Test _convert_from_dynamodb_format handles nested dictionaries."""
    item = {
        "userId": "user-123",
        "profile": {
            "age": Decimal("30"),
            "rating": Decimal("4.5"),
            "name": "Alice",
        },
    }

    result = _convert_from_dynamodb_format(item)

    assert result["userId"] == "user-123"
    assert isinstance(result["profile"]["age"], int)
    assert isinstance(result["profile"]["rating"], float)
    assert result["profile"]["name"] == "Alice"
    assert result["profile"]["age"] == 30
    assert result["profile"]["rating"] == 4.5


def test_convert_from_dynamodb_handles_lists_with_decimals():
    """Test _convert_from_dynamodb_format handles lists with Decimals."""
    item = {
        "userId": "user-123",
        "scores": [Decimal("10"), Decimal("20"), Decimal("30")],
        "ratings": [Decimal("4.5"), Decimal("3.8")],
    }

    result = _convert_from_dynamodb_format(item)

    assert result["userId"] == "user-123"
    assert all(isinstance(score, int) for score in result["scores"])
    assert all(isinstance(rating, float) for rating in result["ratings"])
    assert result["scores"] == [10, 20, 30]
    assert result["ratings"] == [4.5, 3.8]


def test_convert_roundtrip_preserves_data():
    """Test converting to DynamoDB and back preserves data."""
    original = {
        "userId": "user-123",
        "userName": "Test User",
        "age": 30,
        "rating": 4.5,
        "isActive": True,
        "profile": {"level": 5, "score": 99.9},
    }

    converted_to_ddb = _convert_to_dynamodb_format(original)
    converted_back = _convert_from_dynamodb_format(converted_to_ddb)

    assert converted_back["userId"] == original["userId"]
    assert converted_back["userName"] == original["userName"]
    assert converted_back["age"] == original["age"]
    assert converted_back["rating"] == original["rating"]
    assert converted_back["isActive"] == original["isActive"]
    assert converted_back["profile"]["level"] == original["profile"]["level"]
    assert converted_back["profile"]["score"] == original["profile"]["score"]
