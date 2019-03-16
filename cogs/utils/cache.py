from functools import lru_cache

cached_functions = []


def cache(*args, **kwargs):
    def decorator(func):
        func = lru_cache(*args, **kwargs)(func)
        cached_functions.append(func)
        return func

    return decorator


def clear_cache():
    for func in cached_functions:
        func.cache_clear()
