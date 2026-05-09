"""
重试装饰器模块
为网络请求等操作提供自动重试功能
"""

import time
import functools
from utils.logger import default_logger
import config


def retry_on_failure(max_retries=None, delay=None, exceptions=(Exception,)):
    """
    重试装饰器：当函数执行失败时自动重试

    Args:
        max_retries: 最大重试次数，默认使用config中的配置
        delay: 重试间隔（秒），默认使用config中的配置
        exceptions: 需要捕获并重试的异常类型元组

    Returns:
        装饰器函数

    Example:
        @retry_on_failure(max_retries=3, delay=2)
        def fetch_data():
            # 可能失败的操作
            pass
    """
    if max_retries is None:
        max_retries = config.MAX_RETRY_TIMES
    if delay is None:
        delay = config.RETRY_DELAY

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None

            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_retries:
                        default_logger.warning(
                            f"{func.__name__} 执行失败 (尝试 {attempt + 1}/{max_retries + 1}): {str(e)}"
                        )
                        default_logger.info(f"等待 {delay} 秒后重试...")
                        time.sleep(delay)
                    else:
                        default_logger.error(
                            f"{func.__name__} 达到最大重试次数，最终失败: {str(e)}"
                        )

            # 所有重试都失败后，抛出最后一次的异常
            raise last_exception

        return wrapper
    return decorator
