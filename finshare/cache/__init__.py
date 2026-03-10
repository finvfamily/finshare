"""
缓存模块

支持:
- 内存缓存（默认）
- Redis缓存（可选）
- 多级缓存

Example:
    >>> from finshare.cache import cached, MemoryCache
    >>>
    >>> @cached(ttl=60)
    >>> def get_stock_price(code: str):
    >>>     # 从API获取价格
    >>>     return price
    >>>
    >>> # 或者使用缓存类
    >>> from finshare.cache import MemoryCache
    >>> cache = MemoryCache(max_size=1000)
    >>> cache.set("key", "value", ttl=60)
"""

from finshare.cache.cache import (
    Cache,
    MemoryCache,
    RedisCache,
    CacheType,
    CacheStrategyType,
    get_cache,
    set_cache,
    generate_cache_key,
)

from finshare.cache.decorator import (
    cached,
    cached_async,
    invalidate_cache,
)

from finshare.cache.strategy import (
    DataType,
    CacheConfig,
    TTLConfig,
    DEFAULT_TTL_CONFIG,
    get_ttl_config,
    set_ttl_config,
    get_data_type_ttl,
)

__all__ = [
    # Cache
    "Cache",
    "MemoryCache",
    "RedisCache",
    "CacheType",
    "CacheStrategyType",
    "get_cache",
    "set_cache",
    "generate_cache_key",
    # Decorator
    "cached",
    "cached_async",
    "invalidate_cache",
    # Strategy
    "DataType",
    "CacheConfig",
    "TTLConfig",
    "DEFAULT_TTL_CONFIG",
    "get_ttl_config",
    "set_ttl_config",
    "get_data_type_ttl",
]
