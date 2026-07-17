from __future__ import annotations

import secrets
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from tests.helpers.type_defs import StrFactory


@pytest.fixture
def test_password() -> StrFactory:
    return secrets.token_urlsafe
