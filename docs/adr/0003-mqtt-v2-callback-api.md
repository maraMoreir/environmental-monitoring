# 3. paho-mqtt 2.x callback API, and AWS IoT as an optional adapter

## Status

Accepted

## Context

The original `sensor.py` used `mqtt.Client()` with no callback API version
and an `on_connect(client, userdata, flags, rc)` signature. paho-mqtt 2.x
(confirmed as the currently installable major version) makes the callback
API version explicit and adds an MQTTv5 `properties` argument to
`on_connect`/`on_message`; the old signature now raises a deprecation
warning and will stop working in a future release.

Separately, the original `aws_iot.py` embedded
`aws_access_key_id='YOUR_ACCESS_KEY'` / `aws_secret_access_key='YOUR_SECRET_KEY'`
placeholders directly in source — a real credential-hygiene problem, and one
that made the module impossible to run or test without editing code.

## Decision

- `MqttReadingBroker` constructs its client with
  `callback_api_version=mqtt.CallbackAPIVersion.VERSION2` and callback
  signatures that accept the `properties` argument.
- `AwsIotPublisher` never embeds credentials. It calls
  `boto3.client("iot-data", ...)` with no explicit key arguments, relying on
  boto3's default credential chain (environment variables, shared
  `~/.aws/credentials`, or an IAM role). A pre-built client can also be
  injected, which is how tests exercise this adapter without touching AWS.
- AWS IoT forwarding is opt-in via `ENVMON_AWS_IOT_ENABLED` (default
  `false`). The Docker Compose demo and the default local run never require
  an AWS account.

## Consequences

- No hardcoded secrets anywhere in the codebase (see
  `tests/infrastructure/test_aws_iot.py::test_no_credentials_are_hardcoded_in_source`).
- Running the full demo costs nothing and needs no AWS setup.
- Anyone who does want real AWS IoT Core forwarding sets
  `ENVMON_AWS_IOT_ENABLED=true` plus the standard AWS credential
  environment variables — no code changes.
