# sources/__init__.py
"""
数据源模块

提供五种数据源实现：
- EastMoneyDataSource: 东方财富（支持历史K线和实时快照）
- TencentDataSource: 腾讯财经（支持历史K线和实时快照）
- SinaDataSource: 新浪财经（仅支持实时快照）
- BaoStockDataSource: BaoStock（支持历史K线）
- TdxDataSource: 通达信（支持历史K线和实时快照）

弹性模块 (M0):
- resilience.smart_cooldown: 智能冷却
- resilience.retry_handler: 重试机制
- resilience.health_probe: 健康探测
- normalizer: 数据格式标准化
"""

from finshare.sources.base_source import BaseDataSource
from finshare.sources.eastmoney_source import EastMoneyDataSource
from finshare.sources.tencent_source import TencentDataSource
from finshare.sources.sina_source import SinaDataSource
from finshare.sources.baostock_source import BaoStockDataSource
from finshare.sources.tdx_source import TdxDataSource
from finshare.sources.manager import DataSourceManager
from finshare.sources.normalizer import DataNormalizer, get_normalizer

# 弹性模块
from finshare.sources.resilience import (
    SmartCooldown,
    cooldown_manager,
    RetryHandler,
    retry_handler,
    HealthProbe,
    health_probe,
)

# 单例模式的数据管理器
_manager_instance = None


def get_data_manager():
    """获取数据源管理器（单例）"""
    global _manager_instance
    if _manager_instance is None:
        _manager_instance = DataSourceManager()
    return _manager_instance


def get_baostock_source():
    """获取 BaoStock 数据源"""
    return BaoStockDataSource()


def get_tdx_source():
    """获取通达信数据源"""
    return TdxDataSource()


__all__ = [
    # 数据源
    "BaseDataSource",
    "EastMoneyDataSource",
    "TencentDataSource",
    "SinaDataSource",
    "BaoStockDataSource",
    "TdxDataSource",
    "DataSourceManager",
    "get_data_manager",
    "get_baostock_source",
    "get_tdx_source",
    # 数据标准化
    "DataNormalizer",
    "get_normalizer",
    # 弹性模块
    "SmartCooldown",
    "cooldown_manager",
    "RetryHandler",
    "retry_handler",
    "HealthProbe",
    "health_probe",
]
