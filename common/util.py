# -*- coding: utf-8 -*-

def wrap_protocol(endpoint, protocol):
    if endpoint is None:
        return None

    wrapped_protocol = 'https://'
    filter_protocol = 'http://'

    if protocol == 'http':
        wrapped_protocol = 'http://'
        filter_protocol = 'https://'

    if endpoint.startswith(wrapped_protocol):
        return endpoint
    elif endpoint.startswith(filter_protocol):
        return wrapped_protocol + endpoint[len(filter_protocol):]
    else:
        return wrapped_protocol + endpoint

