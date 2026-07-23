"""MQTT adapter implementing both ReadingPublisher and ReadingSubscriber.

Built against the paho-mqtt 2.x API, which requires an explicit callback API
version (the implicit VERSION1 default was removed) and passes an extra
`properties` (MQTTv5) argument into `on_connect`/`on_message` callbacks.
See docs/adr/0003-mqtt-v2-callback-api.md.
"""

from __future__ import annotations

import json
import logging
import ssl
from collections.abc import Callable
from typing import Any

import paho.mqtt.client as mqtt

from environmental_monitoring.domain.models import SensorReading

logger = logging.getLogger(__name__)

_PUBLISH_TIMEOUT_SECONDS = 5


class MqttReadingBroker:
    """Publishes/subscribes `SensorReading`s over MQTT as JSON payloads."""

    def __init__(
        self,
        host: str,
        port: int = 1883,
        *,
        topic: str = "sensors/readings",
        client_id: str = "",
        keepalive: int = 60,
        use_tls: bool = False,
        ca_cert_path: str | None = None,
        client: mqtt.Client | None = None,
    ) -> None:
        self._host = host
        self._port = port
        self._topic = topic
        self._keepalive = keepalive
        self._client = client or mqtt.Client(
            callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
            client_id=client_id,
        )
        if use_tls:
            self._client.tls_set(ca_certs=ca_cert_path, cert_reqs=ssl.CERT_REQUIRED)

    def connect(self) -> None:
        self._client.on_connect = _log_connect
        self._client.connect(self._host, self._port, self._keepalive)
        self._client.loop_start()

    def disconnect(self) -> None:
        self._client.loop_stop()
        self._client.disconnect()

    def publish(self, reading: SensorReading) -> None:
        payload = json.dumps(reading.to_dict())
        info = self._client.publish(self._topic, payload, qos=1)
        info.wait_for_publish(timeout=_PUBLISH_TIMEOUT_SECONDS)

    def subscribe(self, on_reading: Callable[[SensorReading], None]) -> None:
        """Block, dispatching each valid incoming reading to `on_reading`."""

        def _on_message(_client: mqtt.Client, _userdata: Any, msg: mqtt.MQTTMessage) -> None:
            try:
                payload = json.loads(msg.payload.decode("utf-8"))
                reading = SensorReading.from_dict(payload)
            except (
                json.JSONDecodeError,
                KeyError,
                TypeError,
                ValueError,
                UnicodeDecodeError,
            ) as exc:
                logger.warning("Discarding malformed MQTT message on %s: %s", msg.topic, exc)
                return
            on_reading(reading)

        def _on_connect_and_subscribe(
            client: mqtt.Client, userdata: Any, flags: Any, reason_code: Any, properties: Any = None
        ) -> None:
            _log_connect(client, userdata, flags, reason_code, properties)
            client.subscribe(self._topic, qos=1)

        self._client.on_connect = _on_connect_and_subscribe
        self._client.on_message = _on_message
        self._client.connect(self._host, self._port, self._keepalive)
        self._client.loop_forever()


def _log_connect(
    _client: mqtt.Client, _userdata: Any, _flags: Any, reason_code: Any, _properties: Any = None
) -> None:
    logger.info("MQTT connect result: %s", reason_code)
