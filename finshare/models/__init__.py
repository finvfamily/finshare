"""
finshare Models Module

数据模型模块，提供金融数据结构定义。

主要模型：
- HistoricalData: 历史K线数据
- SnapshotData: 实时快照数据
- DataSourceStatus: 数据源状态
"""

from finshare.models.data_models import (
    HistoricalData,
    SnapshotData,
    DataSourceStatus,
    AdjustmentType,
    MarketType,
    FrequencyType,
    MinuteData,
)

# 为了兼容性，提供别名
KLineData = HistoricalData
StockInfo = SnapshotData
MarketData = HistoricalData

__all__ = [
    "HistoricalData",
    "SnapshotData",
    "DataSourceStatus",
    "AdjustmentType",
    "MarketType",
    "FrequencyType",
    "MinuteData",
    # 别名
    "KLineData",
    "StockInfo",
    "MarketData",
]
