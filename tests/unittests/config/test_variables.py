# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.

"""Tests for CORS origin generation."""

from recnavi.config.variables import _get_cors_origins


DOMAINS = ("rec-navi.com",)
SCHEME = "https"
LOCAL_ORIGINS = ["http://localhost:5173", "http://127.0.0.1:5173"]


def test_dev_env_allows_dev_origin() -> None:
    origins = _get_cors_origins(env="dev", domains=DOMAINS)
    assert origins == [*LOCAL_ORIGINS, f"{SCHEME}://dev.rec-navi.com"]


def test_service_env_allows_service_origin() -> None:
    origins = _get_cors_origins(env="service", domains=DOMAINS)
    assert origins == [*LOCAL_ORIGINS, f"{SCHEME}://service.rec-navi.com"]


def test_local_and_ci_only_allow_localhost() -> None:
    for env in ("LOCAL", "LOCAL_CONTAINER", "CI"):
        assert _get_cors_origins(env=env, domains=DOMAINS) == LOCAL_ORIGINS


def test_multiple_domains_each_get_an_origin() -> None:
    origins = _get_cors_origins(env="dev", domains=("a.test", "b.test"))
    assert origins[2:] == [f"{SCHEME}://dev.a.test", f"{SCHEME}://dev.b.test"]


def test_no_per_character_origins() -> None:
    origins = _get_cors_origins(env="dev", domains=DOMAINS)
    assert f"{SCHEME}://dev.r" not in origins
