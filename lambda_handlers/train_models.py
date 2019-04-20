import os
from commons.logger import logged

@logged(truncate_long_messages=False)
def run(fingerprint, context):
    """
    This lambda will add a fingerprint to the DynamoDB table
    Where the train data is stored.
    """

    return {
        'statusCode': 200
    }
