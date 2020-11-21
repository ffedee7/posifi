import boto3
import pandas as pd
from commons.logger import logged
from dynamodb_json import json_util as json_d

client = boto3.client('dynamodb', region_name='sa-east-1')


def get_all_elements_from_table(table_name):
    paginator = client.get_paginator('scan')
    operation_parameters = {
        'TableName': table_name
    }

    page_iterator = paginator.paginate(**operation_parameters)
    df = pd.DataFrame()
    for page in page_iterator:
        df = df.append(
            pd.DataFrame((json_d.loads(page['Items']))),
            sort=False
        )

    return df


@logged()
def add_element_to_table(table_name, content):
    return client.put_item(
        TableName=table_name,
        Item=json_d.dumps(content, as_dict=True)
    )


@logged()
def get_element_of_entity_from_table(table_name, entity, id):
    Key = json.loads(json_d.dumps({'type': entity, 'id': id}))
    return client.get_item(TableName=table_name, Key=Key)


@logged()
def delete_element_of_entity_form_table(table_name, entity, id):
    Key = json.loads(json_d.dumps({'type': entity, 'id': id}))
    return client.delete_item(TableName=table_name, Key=Key)


@logged()
def list_elements_of_table_from_table(table_name, entity):
    paginator = client.get_paginator('query')
    operation_parameters = {
        'TableName': table_name,
        "KeyConditionExpression": "#d0a30 = :d0a30",
        "ExpressionAttributeNames": {"#d0a30": "type"},
        "ExpressionAttributeValues": {":d0a30": {"S": entity}}
    }

    page_iterator = paginator.paginate(**operation_parameters)
    items = []
    for page in page_iterator:
        items.extend(json_d.loads(page['Items']))
    return items
