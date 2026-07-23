from __future__ import annotations

from environmental_monitoring.domain.locations import BRAZIL_STATE_CAPITALS


def test_covers_all_27_brazilian_states() -> None:
    assert len(BRAZIL_STATE_CAPITALS) == 27


def test_state_codes_are_unique() -> None:
    codes = [loc.state_code for loc in BRAZIL_STATE_CAPITALS]
    assert len(codes) == len(set(codes))


def test_sensor_ids_are_unique_and_prefixed() -> None:
    sensor_ids = [loc.sensor_id for loc in BRAZIL_STATE_CAPITALS]
    assert len(sensor_ids) == len(set(sensor_ids))
    assert all(sid.startswith("br-") for sid in sensor_ids)


def test_coordinates_are_within_brazil_bounding_box() -> None:
    for loc in BRAZIL_STATE_CAPITALS:
        assert -35.0 <= loc.latitude <= 6.0
        assert -75.0 <= loc.longitude <= -32.0


def test_label_combines_capital_and_state_code() -> None:
    sp = next(loc for loc in BRAZIL_STATE_CAPITALS if loc.state_code == "SP")
    assert sp.label == "São Paulo, SP"
