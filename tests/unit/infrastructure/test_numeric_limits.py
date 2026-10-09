from os import environ
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

environ.setdefault("DATABASE_URL", "postgresql+psycopg2://bootcamp:bootcamp@localhost:5432/bootcamp")

from calculations import XpGain
from controllers.base_controller import BaseController
from controllers.gamification_controller import GamificationController
from errors import NumericLimitExceeded


MAXIMUM = 9223372036854775807


def test_numeric_boundaries_are_accepted():
    BaseController.check_numeric_limits(0, 1, MAXIMUM)


def test_numeric_overflow_is_a_project_error():
    with pytest.raises(NumericLimitExceeded) as result:
        BaseController.check_numeric_limits(MAXIMUM + 1)
    assert (result.value.http_status, result.value.code) == (422, "QIT001032")


def test_xp_overflow_precedes_every_progress_write():
    controller = GamificationController.__new__(GamificationController)
    controller.gamification_repository = Mock()
    account = SimpleNamespace(level=10, points_free=0)
    with pytest.raises(NumericLimitExceeded):
        controller._apply_xp_gain(account, XpGain(10, MAXIMUM + 1, 1, 0), "TRANSFER_SENT", None, None)
    assert controller.gamification_repository.mock_calls == []
