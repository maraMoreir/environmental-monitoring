from __future__ import annotations

from environmental_monitoring.infrastructure.simulator import SimulatedSensor


def test_seeded_simulator_is_deterministic() -> None:
    a = SimulatedSensor("sensor-001", seed=42)
    b = SimulatedSensor("sensor-001", seed=42)

    readings_a = [a.read() for _ in range(10)]
    readings_b = [b.read() for _ in range(10)]

    for ra, rb in zip(readings_a, readings_b, strict=True):
        assert ra.pm2_5 == rb.pm2_5
        assert ra.pm10 == rb.pm10
        assert ra.temperature_celsius == rb.temperature_celsius
        assert ra.humidity_percent == rb.humidity_percent


def test_readings_are_physically_plausible_and_valid() -> None:
    sensor = SimulatedSensor("sensor-001", seed=1)
    readings = [sensor.read() for _ in range(50)]

    for reading in readings:
        assert reading.pm10 >= reading.pm2_5
        assert 0.0 <= reading.humidity_percent <= 100.0  # type: ignore[operator]
        assert -10.0 <= reading.temperature_celsius <= 45.0  # type: ignore[operator]


def test_walk_produces_varying_values_not_static_noise() -> None:
    sensor = SimulatedSensor("sensor-001", seed=7)
    pm2_5_values = {sensor.read().pm2_5 for _ in range(20)}

    assert len(pm2_5_values) > 1
