import json
import os
import uuid

from commons.aws.dynamodb_helper import add_element_to_table
from commons.logger import logged, logger

DYNAMO_TABLE = os.environ['DYNAMODB_INFORMATION']

@logged(truncate_long_messages=False)
def run(event, context):
    """
    This lambda will get one information from the DynamoDB table
    Where the information of the app is stored.
    """
    body = json.loads(event['body'])

    if not body:
        return {
            'body': json.dumps({
                'message': 'Error creating Information'
            }),
            'statusCode': 400
        }
    body['id'] = str(uuid.uuid1())

    add_element_to_table(DYNAMO_TABLE, body)

    return {
        'body': json.dumps({
            'message': 'Information created successfully'
        }),
        'statusCode': 200
    }
