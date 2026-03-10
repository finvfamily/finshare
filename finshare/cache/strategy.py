"""
缓存策略

提供不同数据类型的TTL策略配置。
"""

from enum import Enum
from typing import Optional, Dict, Any
from dataclasses import dataclass, field


class DataType(Enum):
    """数据类型"""
    SNAPSHOT = "snapshot"      # 实时快照
    DAILY = "daily"           # 日线数据
    MINUTE = "minute"         # 分钟线数据
    FINANCIAL = "financial"    # 财务数据
    FEATURE = "feature"       # 特色数据
    INFO = "info"             # 股票信息


# 默认TTL配置（秒）
DEFAULT_TTL_CONFIG: Dict[DataType, int] = {
    DataType.SNAPSHOT: 5,        # 实时行情: 5秒
    DataType.DAILY: 604800,      # 日线数据: 7天
    DataType.MINUTE: 86400,      # 分钟线: 1天
    DataType.FINANCIAL: 3600,    # 财务数据: 1小时
    DataType.FEATURE: 300,       # 特色数据: 5分钟
    DataType.INFO: 86400,        # 股票信息: 1天
}


@dataclass
class CacheConfig:
    """缓存配置"""
    ttl: int = 300                    # 默认TTL（秒）
    max_size: int = 1000              # 最大缓存条目数
    cache_type: str = "memory"        # 缓存类型
    enable_cache: bool = True         # 是否启用缓存
    redis_host: str = "localhost"     # Redis主机
    redis_port: int = 6379            # Redis端口
    redis_db: int = 0                # Redis数据库
    redis_password: Optional[str] = None  # Redis密码


@dataclass
class TTLConfig:
    """TTL配置"""
    snapshot_ttl: int = 5             # 实时行情
    daily_ttl: int = 604800          # 日线数据 (7天)
    minute_ttl: int = 86400          # 分钟线 (1天)
    financial_ttl: int = 3600        # 财务数据 (1小时)
    feature_ttl: int = 300           # 特色数据 (5分钟)
    info_ttl: int = 86400            # 股票信息 (1天)

    def get_ttl(self, data_type: DataType) -> int:
        """获取指定数据类型的TTL"""
        ttl_map = {
            DataType.SNAPSHOT: self.snapshot_ttl,
            DataType.DAILY: self.daily_ttl,
            DataType.MINUTE: self.minute_ttl,
            DataType.FINANCIAL: self.financial_ttl,
            DataType.FEATURE: self.feature_ttl,
            DataType.INFO: self.info_ttl,
        }
        return ttl_map.get(data_type, 300)


# 全局TTL配置
_ttl_config: TTLConfig = TTLConfig()


def get_ttl_config() -> TTLConfig:
    """获取TTL配置"""
    return _ttl_config


def set_ttl_config(config: TTLConfig) -> None:
    """设置TTL配置"""
    global _ttl_config
    _ttl_config = config


def get_data_type_ttl(data_type: DataType) -> int:
    """
    获取数据类型对应的TTL

    Args:
        data_type: 数据类型

    Returns:
        TTL（秒）
    """
    return _ttl_config.get_ttl(data_type)


__all__ = [
    "DataType",
    "CacheConfig",
    "TTLConfig",
    "DEFAULT_TTL_CONFIG",
    "get_ttl_config",
    "set_ttl_config",
    "get_data_type_ttl",
]
