import json
import os

from commons.aws.dynamodb_helper import delete_element_form_table
from commons.logger import logged, logger
from commons.decimal_encoder import DecimalEncoder
DYNAMO_TABLE = os.environ['DYNAMODB_INFORMATION']


@logged(truncate_long_messages=False)
def run(event, context):
    """
    This lambda will get one information from the DynamoDB table
    Where the information of the app is stored.
    """
    information_id = event['pathParameters']['id']

    if not information_id:
        return {
            'body': json.dumps({
                'message': 'Error deleting Information'
            }),
            'statusCode': 400
        }

    delete_element_form_table(DYNAMO_TABLE, information_id)

    return {
        'body': json.dumps({
            'message': 'Information deleted successfully'
        }),
        'statusCode': 200
    }
