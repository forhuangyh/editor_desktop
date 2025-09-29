import cProfile
import pstats
import io
import time
import functools


def timer_trace(func):
    """
    一个用于计算函数执行时间的装饰器
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        print(f"方法 {func.__name__} 执行耗时: {end_time - start_time:.4f} 秒")
        return result
    return wrapper


def run_with_profile(func):
    """
    一个用于对整个函数执行进行性能分析的装饰器
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        pr = cProfile.Profile()
        pr.enable()

        result = func(*args, **kwargs)

        pr.disable()
        s = io.StringIO()
        sortby = 'cumulative'  # 或 'tottime'
        ps = pstats.Stats(pr, stream=s).sort_stats(sortby)
        ps.print_stats()
        print(s.getvalue())

        return result
    return wrapper
