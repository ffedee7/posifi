import os
import io
import boto3
import json

from commons.logger import logged

S3_CLIENT = boto3.session.Session().client('s3')


def get_file(bucket_name, key):
    try:
        json_obj = S3_CLIENT.get_object(Bucket=bucket_name, Key=key)
        return json_obj['Body'].read()
    except S3_CLIENT.exceptions.NoSuchKey:
        return None


@logged
def get_json(bucket_name, key):
    try:
        json_obj = S3_CLIENT.get_object(Bucket=bucket_name, Key=key)
        return json.loads(json_obj['Body'].read().decode())
    except S3_CLIENT.exceptions.NoSuchKey:
        return None


def put_file(bucket_name, key, upload_file):
    file_like = io.BytesIO(upload_file)
    S3_CLIENT.upload_fileobj(file_like, bucket_name, key)


@logged
def put_json(bucket_name, key, json_dict, public_read=False):
    """
    Upload the object `obj` to the S3 bucket under the key `key`.
    The object is serialized as JSON with UTF-8 encoding

    Params
    ------
    key:      the key under which the object is going to be uploaded
    obj:      the object to be uploaded
    """

    file_like = io.BytesIO(json.dumps(
        json_dict,
        separators=[",", ":"]
    ).encode("utf-8"))

    extra_args = {}
    if public_read:
        extra_args = {'ACL': 'public-read'}

    S3_CLIENT.upload_fileobj(file_like, bucket_name, key, ExtraArgs=extra_args)

    return f'{S3_CLIENT.meta.endpoint_url}/{bucket_name}/{key}'