def paginate(method, **kwargs):
    client = method.__self__
    paginator = client.get_paginator(method.__name__)
    return (
        result
        for page in paginator.paginate(**kwargs).result_key_iters()
        for result in page
    )