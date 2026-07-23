from __future__ import annotations

import json
from unittest.mock import MagicMock

from environmental_monitoring.domain.models import SensorReading
from environmental_monitoring.infrastructure.mqtt_broker import MqttReadingBroker


def _make_broker() -> tuple[MqttReadingBroker, MagicMock]:
    mock_client = MagicMock()
    broker = MqttReadingBroker("localhost", topic="sensors/readings", client=mock_client)
    return broker, mock_client


def test_connect_starts_the_network_loop() -> None:
    broker, mock_client = _make_broker()

    broker.connect()

    mock_client.connect.assert_called_once_with("localhost", 1883, 60)
    mock_client.loop_start.assert_called_once()


def test_publish_sends_json_payload(valid_reading: SensorReading) -> None:
    broker, mock_client = _make_broker()

    broker.publish(valid_reading)

    args, kwargs = mock_client.publish.call_args
    assert args[0] == "sensors/readings"
    assert json.loads(args[1]) == valid_reading.to_dict()
    assert kwargs == {"qos": 1}
    mock_client.publish.return_value.wait_for_publish.assert_called_once()


def test_subscribe_decodes_valid_message_and_invokes_callback(valid_reading: SensorReading) -> None:
    broker, mock_client = _make_broker()
    received: list[SensorReading] = []

    broker.subscribe(received.append)
    on_message = mock_client.on_message
    message = MagicMock(
        topic="sensors/readings", payload=json.dumps(valid_reading.to_dict()).encode()
    )

    on_message(mock_client, None, message)

    assert received == [valid_reading]


def test_subscribe_discards_malformed_message() -> None:
    broker, mock_client = _make_broker()
    received: list[SensorReading] = []

    broker.subscribe(received.append)
    on_message = mock_client.on_message
    message = MagicMock(topic="sensors/readings", payload=b"not-json")

    on_message(mock_client, None, message)  # must not raise

    assert received == []


def test_disconnect_stops_the_network_loop() -> None:
    broker, mock_client = _make_broker()

    broker.disconnect()

    mock_client.loop_stop.assert_called_once()
    mock_client.disconnect.assert_called_once()
