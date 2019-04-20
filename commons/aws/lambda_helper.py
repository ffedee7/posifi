import json
import boto3

from commons.logger import logged

# Create the boto3 lambda client
lambda_client = boto3.session.Session().client('lambda')


@logged()
def invoke_async(lambda_name, payload):
    payload_dump = payload if payload else json.dumps(payload)
    return lambda_client.invoke(
        InvocationType='Event',
        FunctionName=lambda_name,
        Payload=payload_dump
    )


@logged
def invoke_sync(lambda_name, payload):
    return json.loads(lambda_client.invoke(
        InvocationType='RequestResponse',
        FunctionName=lambda_name,
        Payload=json.dumps(payload)
    )['Payload'].read())
