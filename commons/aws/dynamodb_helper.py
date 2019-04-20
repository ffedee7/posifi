import boto3
import pandas as pd
from commons.logger import logged
from dynamodb_json import json_util as json_d

client = boto3.client('dynamodb')

def get_all_elements_from_table(table_name):
    paginator = client.get_paginator('scan')
    operation_parameters = {
        'TableName': table_name
    }

    page_iterator = paginator.paginate(**operation_parameters)
    df = pd.DataFrame()
    for page in page_iterator:
        df = df.append(json_d.loads(page['Items']))

    return df


@logged()
def add_element_to_table(table_name, content):
    return client.put_item(
        TableName=table_name,
        Item=json_d.dumps(content, as_dict=True)
    )