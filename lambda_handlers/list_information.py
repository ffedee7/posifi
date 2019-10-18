import json
import os

from commons.aws.dynamodb_helper import list_elements_from_table
from commons.logger import logged, logger
from commons.decimal_encoder import DecimalEncoder

DYNAMO_TABLE = os.environ['DYNAMODB_INFORMATION']

@logged(truncate_long_messages=False)
def run(event, context):
    """
    This lambda will get one information from the DynamoDB table
    Where the information of the app is stored.
    """
    result = list_elements_from_table(DYNAMO_TABLE)

    return {
        'body': json.dumps(result, cls=DecimalEncoder),
        'statusCode': 200
    }
