import json
import time
import os

from commons.aws.dynamodb_helper import add_element_to_table
from commons.logger import logged
from commons.settings import settings

DYNAMO_TABLE = os.environ['DYNAMODB_FINGERPRINTS']

MAC_WHITELIST = settings['MAC_WHITELIST'].split(',')


@logged(truncate_long_messages=False)
def run(event, context):
    """
    This lambda will add a fingerprint to the DynamoDB table
    Where the train data is stored.
    """
    fingerprint = json.loads(event['body'])
    current_timestamp = int(time.time())

    fingerprint = {mac:rss for mac,rss in fingerprint.items() if mac in MAC_WHITELIST}

    fingerprint['timestamp'] = current_timestamp

    add_element_to_table(DYNAMO_TABLE, fingerprint)

    return {
        'body': json.dumps({
            'message': 'Fingerprint added successfully'
        }),
        'statusCode': 200
    }
