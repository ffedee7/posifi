import json

from commons.logger import logged
from commons.ai_engine import AIEngine

@logged(truncate_long_messages=False)
def run(event, context):
    """
    This lambda will use a fingerprint to locate
    where an user is located.
    """

    body = json.loads(event['body'])
    has_5_ghz = body.get('has_5_ghz', False)

    ai_engine = AIEngine(has_5_ghz)

    fingeprint = ai_engine.prepare_fingerprint(body)

    location_label = ai_engine.localize_fingerprint(fingeprint)

    return {
        'body': json.dumps({
            'location': location_label
        }),
        'statusCode': 200
    }
