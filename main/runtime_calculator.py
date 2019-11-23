import functools
import time


def timer(func):

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.perf_counter()
        value = func(*args, **kwargs)
        end_time = time.perf_counter()
        run_time = end_time - start_time
        print(f"Task finished in {round(run_time, 3)} secs")
        return value

    return wrapper