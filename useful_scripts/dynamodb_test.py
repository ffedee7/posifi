import boto3
import pandas as pd
from dynamodb_json import json_util as json

client = boto3.client('dynamodb')

paginator = client.get_paginator('scan')
operation_parameters = {
  'TableName': 'test'
}

page_iterator = paginator.paginate(**operation_parameters)
for page in page_iterator:
    df = pd.DataFrame(json.loads(page['Items']))