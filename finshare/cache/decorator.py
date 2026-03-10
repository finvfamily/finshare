"""
缓存装饰器

提供函数缓存装饰器，支持TTL和自定义缓存键生成。
"""

import time
import hashlib
import functools
from typing import Any, Optional, Callable, Union
from datetime import datetime, timedelta

from finshare.cache.cache import get_cache, Cache


def cached(
    ttl: Optional[int] = None,
    key_prefix: str = "",
    cache_type: str = "memory",
    max_size: int = 1000,
) -> Callable:
    """
    缓存装饰器

    Args:
        ttl: 缓存过期时间（秒），默认不过期
        key_prefix: 缓存键前缀
        cache_type: 缓存类型 ("memory" 或 "redis")
        max_size: 内存缓存最大条目数

    Returns:
        装饰后的函数

    Example:
        @cached(ttl=60, key_prefix="stock_")
        def get_stock_price(code: str) -> float:
            # 从API获取价格
            return price
    """
    def decorator(func: Callable) -> Callable:
        # 获取缓存实例
        cache = get_cache(cache_type, max_size=max_size)

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # 生成缓存键
            if key_prefix:
                key = f"{key_prefix}{func.__name__}"
            else:
                key = func.__name__

            # 添加函数参数到缓存键
            key_data = f"{key}:{args}:{sorted(kwargs.items())}"
            cache_key = hashlib.md5(key_data.encode()).hexdigest()

            # 尝试从缓存获取
            cached_value = cache.get(cache_key)
            if cached_value is not None:
                return cached_value

            # 调用原函数
            result = func(*args, **kwargs)

            # 存入缓存
            cache.set(cache_key, result, ttl=ttl)

            return result

        # 添加缓存管理方法
        wrapper.clear_cache = lambda: cache.clear()
        wrapper.cache = cache

        return wrapper

    return decorator


def cached_async(
    ttl: Optional[int] = None,
    key_prefix: str = "",
    cache_type: str = "memory",
    max_size: int = 1000,
) -> Callable:
    """
    异步函数缓存装饰器

    Args:
        ttl: 缓存过期时间（秒），默认不过期
        key_prefix: 缓存键前缀
        cache_type: 缓存类型 ("memory" 或 "redis")
        max_size: 内存缓存最大条目数

    Returns:
        装饰后的异步函数
    """
    def decorator(func: Callable) -> Callable:
        # 获取缓存实例
        cache = get_cache(cache_type, max_size=max_size)

        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # 生成缓存键
            if key_prefix:
                key = f"{key_prefix}{func.__name__}"
            else:
                key = func.__name__

            # 添加函数参数到缓存键
            key_data = f"{key}:{args}:{sorted(kwargs.items())}"
            cache_key = hashlib.md5(key_data.encode()).hexdigest()

            # 尝试从缓存获取
            cached_value = cache.get(cache_key)
            if cached_value is not None:
                return cached_value

            # 调用原函数
            result = await func(*args, **kwargs)

            # 存入缓存
            cache.set(cache_key, result, ttl=ttl)

            return result

        # 添加缓存管理方法
        wrapper.clear_cache = lambda: cache.clear()
        wrapper.cache = cache

        return wrapper

    return decorator


def invalidate_cache(key_pattern: str = "", cache: Optional[Cache] = None) -> int:
    """
    清除匹配的缓存

    Args:
        key_pattern: 缓存键匹配模式（支持通配符）
        cache: 缓存实例，默认使用全局缓存

    Returns:
        删除的缓存数量
    """
    if cache is None:
        cache = get_cache()

    if not key_pattern:
        return 1 if cache.clear() else 0

    # 查找匹配的键并删除
    count = 0
    for key in cache.keys():
        if key_pattern in key or key_pattern.replace("*", "") in key:
            if cache.delete(key):
                count += 1

    return count


__all__ = ["cached", "cached_async", "invalidate_cache"]
