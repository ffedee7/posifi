import json
import time
import os

from commons.aws.dynamodb_helper import add_element_to_table
from commons.logger import logged, logger
# from commons.settings import settings

DYNAMO_TABLE = os.environ['DYNAMODB_FINGERPRINTS']

# MAC_WHITELIST = settings['MAC_WHITELIST'].split(',')


@logged(truncate_long_messages=False)
def run(event, context):
    """
    This lambda will add a fingerprint to the DynamoDB table
    Where the train data is stored.
    """
    body = json.loads(event['body'])
    current_timestamp = int(time.time())

    unfiltered_fingerprint = body.get('wifi', {})
    unfiltered_fingerprint.update(body.get('bt', {}))

    # fingerprint = {mac:rss for mac,rss in unfiltered_fingerprint.items() if mac in MAC_WHITELIST}

    if not fingerprint:
        return {
            'body': json.dumps({
                'message': 'Error adding Fingerprint'
            }),
            'statusCode': 400
        }

    unfiltered_fingerprint['timestamp'] = current_timestamp
    unfiltered_fingerprint['result'] = body['result']

    add_element_to_table(DYNAMO_TABLE, unfiltered_fingerprint)

    return {
        'body': json.dumps({
            'message': 'Fingerprint added successfully'
        }),
        'statusCode': 200
    }
