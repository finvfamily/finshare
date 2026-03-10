"""
缓存模块

支持:
- 内存缓存（默认）
- Redis缓存（可选）
- 多级缓存
"""

import time
import hashlib
import pickle
import threading
from abc import ABC, abstractmethod
from typing import Any, Optional, Dict, Callable, Union
from datetime import datetime, timedelta
from functools import wraps
from enum import Enum

from finshare.logger import logger


class CacheType(Enum):
    """缓存类型"""
    MEMORY = "memory"
    REDIS = "redis"


class CacheStrategyType(Enum):
    """缓存策略类型"""
    TTL = "ttl"  # Time To Live
    LRU = "lru"  # Least Recently Used
    LFU = "lfu"  # Least Frequently Used


class Cache(ABC):
    """缓存抽象基类"""

    @abstractmethod
    def get(self, key: str) -> Optional[Any]:
        """获取缓存"""
        pass

    @abstractmethod
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """设置缓存"""
        pass

    @abstractmethod
    def delete(self, key: str) -> bool:
        """删除缓存"""
        pass

    @abstractmethod
    def clear(self) -> bool:
        """清空缓存"""
        pass

    @abstractmethod
    def exists(self, key: str) -> bool:
        """检查键是否存在"""
        pass


class MemoryCache(Cache):
    """内存缓存实现"""

    def __init__(self, max_size: int = 1000):
        """
        初始化内存缓存

        Args:
            max_size: 最大缓存条目数
        """
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._max_size = max_size
        self._lock = threading.RLock()

    def get(self, key: str) -> Optional[Any]:
        """获取缓存"""
        with self._lock:
            item = self._cache.get(key)
            if item is None:
                return None

            # 检查是否过期
            if item["expire_at"] and item["expire_at"] < time.time():
                del self._cache[key]
                return None

            # 更新访问时间
            item["accessed_at"] = time.time()
            item["access_count"] = item.get("access_count", 0) + 1
            return item["value"]

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """设置缓存"""
        with self._lock:
            # 如果缓存已满，删除最旧的条目
            if len(self._cache) >= self._max_size:
                self._evict_oldest()

            expire_at = None
            if ttl and ttl > 0:
                expire_at = time.time() + ttl

            self._cache[key] = {
                "value": value,
                "created_at": time.time(),
                "expire_at": expire_at,
                "accessed_at": time.time(),
                "access_count": 0,
            }
            return True

    def delete(self, key: str) -> bool:
        """删除缓存"""
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False

    def clear(self) -> bool:
        """清空缓存"""
        with self._lock:
            self._cache.clear()
            return True

    def exists(self, key: str) -> bool:
        """检查键是否存在"""
        return self.get(key) is not None

    def _evict_oldest(self):
        """删除最旧的缓存条目"""
        if not self._cache:
            return

        # 删除最早访问的条目
        oldest_key = min(
            self._cache.keys(),
            key=lambda k: self._cache[k]["accessed_at"]
        )
        del self._cache[oldest_key]

    def size(self) -> int:
        """获取缓存大小"""
        with self._lock:
            return len(self._cache)

    def keys(self) -> list:
        """获取所有键"""
        with self._lock:
            return list(self._cache.keys())


class RedisCache(Cache):
    """Redis缓存实现（可选）"""

    def __init__(self, host: str = "localhost", port: int = 6379, db: int = 0, password: Optional[str] = None):
        """
        初始化Redis缓存

        Args:
            host: Redis主机地址
            port: Redis端口
            db: 数据库编号
            password: 密码
        """
        try:
            import redis
            self._redis = redis.Redis(
                host=host,
                port=port,
                db=db,
                password=password,
                decode_responses=False
            )
            self._enabled = True
        except ImportError:
            logger.warning("redis库未安装，Redis缓存不可用")
            self._enabled = False
            self._redis = None

    def get(self, key: str) -> Optional[Any]:
        """获取缓存"""
        if not self._enabled:
            return None
        try:
            value = self._redis.get(key)
            if value:
                return pickle.loads(value)
            return None
        except Exception as e:
            logger.warning(f"Redis get失败: {e}")
            return None

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """设置缓存"""
        if not self._enabled:
            return False
        try:
            serialized = pickle.dumps(value)
            if ttl and ttl > 0:
                self._redis.setex(key, ttl, serialized)
            else:
                self._redis.set(key, serialized)
            return True
        except Exception as e:
            logger.warning(f"Redis set失败: {e}")
            return False

    def delete(self, key: str) -> bool:
        """删除缓存"""
        if not self._enabled:
            return False
        try:
            self._redis.delete(key)
            return True
        except Exception as e:
            logger.warning(f"Redis delete失败: {e}")
            return False

    def clear(self) -> bool:
        """清空缓存"""
        if not self._enabled:
            return False
        try:
            self._redis.flushdb()
            return True
        except Exception as e:
            logger.warning(f"Redis clear失败: {e}")
            return False

    def exists(self, key: str) -> bool:
        """检查键是否存在"""
        if not self._enabled:
            return False
        try:
            return bool(self._redis.exists(key))
        except Exception as e:
            logger.warning(f"Redis exists失败: {e}")
            return False


def generate_cache_key(*args, **kwargs) -> str:
    """生成缓存键"""
    key_data = f"{args}:{sorted(kwargs.items())}"
    return hashlib.md5(key_data.encode()).hexdigest()


# 全局缓存实例
_global_cache: Optional[Cache] = None


def get_cache(cache_type: str = "memory", **kwargs) -> Cache:
    """
    获取缓存实例

    Args:
        cache_type: 缓存类型 ("memory" 或 "redis")
        **kwargs: 缓存初始化参数

    Returns:
        Cache实例
    """
    global _global_cache

    if _global_cache is not None:
        return _global_cache

    if cache_type == "redis":
        _global_cache = RedisCache(**kwargs)
    else:
        max_size = kwargs.get("max_size", 1000)
        _global_cache = MemoryCache(max_size=max_size)

    return _global_cache


def set_cache(cache: Cache) -> None:
    """设置全局缓存实例"""
    global _global_cache
    _global_cache = cache


__all__ = [
    "Cache",
    "MemoryCache",
    "RedisCache",
    "CacheType",
    "CacheStrategyType",
    "get_cache",
    "set_cache",
    "generate_cache_key",
]
