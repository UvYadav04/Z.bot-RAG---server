import functools
import inspect

def safeExecution(fn):

    if inspect.iscoroutinefunction(fn):

        @functools.wraps(fn)
        async def async_wrapper(*args, **kwargs):
            try:
                return await fn(*args, **kwargs)
            except Exception as e:
                print(f"Async error in {fn.__name__}: {e}")
                raise

        return async_wrapper

    else:

        @functools.wraps(fn)
        def sync_wrapper(*args, **kwargs):
            try:
                return fn(*args, **kwargs)
            except Exception as e:
                print(f"Sync error in {fn.__name__}: {e}")
                raise

        return sync_wrapper