import boto3

ssm_client = boto3.session.Session().client('ssm')


def get_parameters_by_path(path='/'):
    # Append the '/' to the end so the split call later don't produce an empty first component
    parameter_store = paginate(
        ssm_client.get_parameters_by_path,
        Path=path,
        Recursive=True,
        WithDecryption=True
    )
    params = {}

    for parameter in parameter_store:
        sub_names = parameter['Name'].replace(path, '').split('/')
        param_node = params

        while sub_names:
            sub_name = sub_names.pop(0)

            if sub_names:
                if not param_node.get(sub_name, None):
                    param_node[sub_name] = {}
                param_node = param_node[sub_name]
            else:
                param_node[sub_name] = parameter['Value']

    return params


def get_all_parameters():
    return get_parameters_by_path('')

def paginate(method, **kwargs):
    client = method.__self__
    paginator = client.get_paginator(method.__name__)
    return (
        result
        for page in paginator.paginate(**kwargs).result_key_iters()
        for result in page
    )
