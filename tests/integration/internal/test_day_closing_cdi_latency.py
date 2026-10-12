from tests.utils import DbUtils, MockGenerator, PayloadGenerator, RequestGenerator


def test_cdi_response_after_three_seconds_still_closes_the_day():
    DbUtils.rollback()
    MockGenerator.set_cdi_delay("2026-06-01", 3)
    try:
        status, body = RequestGenerator.POST_day_closing(PayloadGenerator.day_closing("2026-06-01"))
        assert status == 200, body
        assert body == {"closed_date": "2026-06-01", "accounting_date": "2026-06-02"}
    finally:
        MockGenerator.clear_cdi("2026-06-01")
