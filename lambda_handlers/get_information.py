import json
import os

from commons.aws.dynamodb_helper import get_element_from_table
from commons.logger import logged, logger
from commons.decimal_encoder import DecimalEncoder
from dynamodb_json import json_util as json_d

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
                'message': 'Error getting Information'
            }),
            'statusCode': 400
        }

    result = get_element_from_table(DYNAMO_TABLE, information_id)

    return {
        'body': json.dumps(json_d.loads(result['Item']), cls=DecimalEncoder),
        'statusCode': 200
    }
