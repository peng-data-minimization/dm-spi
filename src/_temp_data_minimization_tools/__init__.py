from collections import Iterable
import statistics
from typing import Callable
from _temp_data_minimization_tools.utils import check_input_type
import hashlib
import datetime


@check_input_type
def drop_keys(data: [dict], keys):
    return _replace_with_function(data, keys, _reset_value)


@check_input_type
def hash_keys(data: [dict], keys, hash_algorithm=hashlib.sha224, salt=None, digest_to_bytes=False):
    if not salt:
        salt = datetime.datetime.now().timestamp()

    return _replace_with_function(data, keys, _hashing_wrapper, hash_algorithm=hash_algorithm,
                                  digest_to_bytes=digest_to_bytes, salt=salt)


@check_input_type
def reduce_to_mean(data: [dict], keys):
    return _replace_with_aggregate(data, keys, statistics.mean)


@check_input_type
def reduce_to_median(data: [dict], keys):
    return _replace_with_aggregate(data, keys, statistics.median)


def _reset_value(value):
    if isinstance(value, str):
        return ""
    if isinstance(value, Iterable):
        return []
    if isinstance(value, int):
        return 0
    # ...


def _replace_with_function(data: [dict], keys_to_apply_to, replace_func: Callable, *func_args, **func_kwargs):
    if isinstance(keys_to_apply_to, str):
        keys_to_apply_to = [keys_to_apply_to]

    for item in data:
        for key in keys_to_apply_to:
            try:
                item[key] = replace_func(item[key], *func_args, **func_kwargs)
            except KeyError:
                pass
    return data


def _replace_with_aggregate(data: [dict], keys_to_aggregate, aggregator: Callable):
    for key in keys_to_aggregate:
        avg = aggregator([item[key] for item in data])
        for item in data:
            item[key] = avg
    return data


def _hashing_wrapper(value, hash_algorithm, salt, digest_to_bytes=False):
    value_str = str(value) + str(salt)
    bytes_rep = value_str.encode('utf8')

    if digest_to_bytes:
        return hash_algorithm(bytes_rep).digest()
    else:
        return hash_algorithm(bytes_rep).hexdigest()