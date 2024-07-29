import json
import boto3
from botocore.exceptions import NoCredentialsError, PartialCredentialsError
from src.utils.config import AWS_REGION, IOT_ENDPOINT, CERTIFICATE_PATH, PRIVATE_KEY_PATH, ROOT_CA_PATH

def connect_aws_iot():
    try:
        client = boto3.client(
            'iot-data',
            region_name=AWS_REGION,
            endpoint_url=IOT_ENDPOINT,
            aws_access_key_id='YOUR_ACCESS_KEY',
            aws_secret_access_key='YOUR_SECRET_KEY'
        )
        print("Conectado ao AWS IoT Core")
        return client
    except (NoCredentialsError, PartialCredentialsError) as e:
        print(f"Erro de credenciais: {e}")
        return None

def publish_to_aws_iot(client, topic, message):
    try:
        response = client.publish(
            topic=topic,
            qos=1,
            payload=message
        )
        print("Mensagem publicada ao AWS IoT Core")
    except Exception as e:
        print(f"Erro ao publicar mensagem: {e}")

# Exemplo de uso
if __name__ == "__main__":
    client = connect_aws_iot()
    if client:
        publish_to_aws_iot(client, "sensor/air_quality", json.dumps({"key": "value"}))
