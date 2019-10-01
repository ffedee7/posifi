import json
import time
import os

from commons.aws.dynamodb_helper import add_element_to_table
from commons.logger import logged, logger
from commons.settings import settings

DYNAMO_TABLE = os.environ['DYNAMODB_INFORMATION']

@logged(truncate_long_messages=False)
def run(event, context):
    """
    This lambda will add the information of a piece to the DynamoDB table
    Where the information of the app is stored.
    """
    body = json.loads(event['body'])

    if not body:
        return {
            'body': json.dumps({
                'message': 'Error adding Information'
            }),
            'statusCode': 400
        }

    add_element_to_table(DYNAMO_TABLE, body)

    return {
        'body': json.dumps({
            'message': 'Information added successfully'
        }),
        'statusCode': 200
    }
