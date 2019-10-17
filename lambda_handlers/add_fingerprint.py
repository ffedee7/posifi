import json
import time
import os

from commons.aws.dynamodb_helper import add_element_to_table
from commons.logger import logged, logger
from commons.settings import settings


## SET IMPORTAN VARIABLES ##

DYNAMO_TABLE = os.environ['DYNAMODB_FINGERPRINTS']
SETTINGS = os.environ['IMPORT_SETTINGS']
if SETTINGS:
    FILTER = settings['FILTER_MACS']
    MAC_WHITELIST = settings['MAC_WHITELIST'].split(',') if FILTER else []
else:
    FILTER = os.environ['FILTER_MACS']
    MAC_WHITELIST = local_settings['MAC_WHITELIST'].split(',') if FILTER else []
###########################


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

    fingerprint = {mac: rss for mac, rss in unfiltered_fingerprint.items(
    ) if mac in MAC_WHITELIST} if FILTER else unfiltered_fingerprint

    if not fingerprint:
        return {
            'body': json.dumps({
                'message': 'Error adding Fingerprint'
            }),
            'statusCode': 400
        }

    fingerprint['timestamp'] = current_timestamp
    fingerprint['result'] = body['result']

    add_element_to_table(DYNAMO_TABLE, fingerprint)

    return {
        'body': json.dumps({
            'message': 'Fingerprint added successfully'
        }),
        'statusCode': 200
    }
