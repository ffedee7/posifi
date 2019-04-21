import json

from commons.logger import logged
from commons.ai_engine import AIEngine

@logged(truncate_long_messages=False)
def run(event, context):
    """
    This lambda will train all the required models.
    """

    try:
        body = json.loads(event['body'])
    except:
        body = event['body']
        
    has_5_ghz = body.get('has_5_ghz', False)

    ai_engine = AIEngine(has_5_ghz)
    ai_engine.train()