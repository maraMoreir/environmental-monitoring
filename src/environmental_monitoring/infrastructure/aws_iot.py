"""AWS IoT Core adapter, forwarding readings over the IoT Data Plane API."""

from __future__ import annotations

import json
from typing import Any

import boto3

from environmental_monitoring.domain.models import SensorReading


class AwsIotPublisher:
    """Publishes readings to an AWS IoT Core topic.

    Credentials are never embedded in code: boto3's default credential chain
    (environment variables, shared config file, or an IAM role) is used
    unless a pre-built client is injected, which also makes this adapter
    testable without touching AWS. Publish failures propagate to the caller
    (`IngestionService` treats cloud forwarding as best-effort and logs them).
    """

    def __init__(
        self,
        topic: str,
        region_name: str,
        endpoint_url: str,
        client: Any | None = None,
    ) -> None:
        self._topic = topic
        self._client = client or boto3.client(
            "iot-data", region_name=region_name, endpoint_url=endpoint_url
        )

    def publish(self, reading: SensorReading) -> None:
        self._client.publish(
            topic=self._topic,
            qos=1,
            payload=json.dumps(reading.to_dict()),
        )
