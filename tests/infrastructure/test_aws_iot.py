from __future__ import annotations

import json
from unittest.mock import MagicMock

import pytest

from environmental_monitoring.domain.models import SensorReading
from environmental_monitoring.infrastructure.aws_iot import AwsIotPublisher


def test_publish_calls_iot_data_client_with_expected_payload(valid_reading: SensorReading) -> None:
    mock_client = MagicMock()
    publisher = AwsIotPublisher(
        topic="sensors/readings",
        region_name="us-east-1",
        endpoint_url="https://example",
        client=mock_client,
    )

    publisher.publish(valid_reading)

    mock_client.publish.assert_called_once()
    _, kwargs = mock_client.publish.call_args
    assert kwargs["topic"] == "sensors/readings"
    assert kwargs["qos"] == 1
    assert json.loads(kwargs["payload"]) == valid_reading.to_dict()


def test_publish_failure_propagates_to_caller(valid_reading: SensorReading) -> None:
    mock_client = MagicMock()
    mock_client.publish.side_effect = RuntimeError("boto3 error")
    publisher = AwsIotPublisher(
        topic="sensors/readings",
        region_name="us-east-1",
        endpoint_url="https://example",
        client=mock_client,
    )

    with pytest.raises(RuntimeError, match="boto3 error"):
        publisher.publish(valid_reading)


def test_no_credentials_are_hardcoded_in_source() -> None:
    import inspect

    from environmental_monitoring.infrastructure import aws_iot

    source = inspect.getsource(aws_iot)
    assert "aws_access_key_id" not in source
    assert "aws_secret_access_key" not in source
