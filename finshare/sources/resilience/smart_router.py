"""
智能路由模块

根据数据类型选择最佳数据源。
"""

import time
from enum import Enum
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime

from finshare.logger import logger


class DataType(Enum):
    """数据类型"""
    SNAPSHOT = "snapshot"        # 实时快照
    DAILY = "daily"              # 日线数据
    MINUTE = "minute"            # 分钟线
    FINANCIAL = "financial"      # 财务数据
    MONEY_FLOW = "money_flow"    # 资金流向
    LHB = "lhb"                  # 龙虎榜
    MARGIN = "margin"            # 融资融券
    INFO = "info"                # 股票信息
    STOCK_LIST = "stock_list"    # 证券列表
    VALUATION = "valuation"      # 估值数据
    INDUSTRY = "industry"        # 行业分类
    DIVIDEND = "dividend"        # 分红数据
    GLOBAL_INDEX = "global_index"  # 全球指数
    # 新增数据类型
    CONCEPT_LIST = "concept_list"              # 概念板块列表
    CONCEPT_CONSTITUENTS = "concept_constituents"  # 概念板块成分股
    CONCEPT_MONEY_FLOW = "concept_money_flow"  # 概念板块资金流向
    MONEY_FLOW_STOCK = "money_flow_stock"      # 个股资金流向
    EARNINGS_CALENDAR = "earnings_calendar"    # 业绩预告日历
    EARNINGS_PREANNOUNCE = "earnings_preannounce"  # 业绩预告
    MARKET_OVERVIEW = "market_overview"        # 市场概览
    MARGIN_SUMMARY = "margin_summary"          # 融资融券汇总


class SourceType(Enum):
    """数据源类型"""
    EASTMONEY = "eastmoney"
    TENCENT = "tencent"
    SINA = "sina"
    TDX = "tdx"
    BAOSTOCK = "baostock"
    PLAYWRIGHT_EASTMONEY = "playwright_eastmoney"
    PLAYWRIGHT_SINA = "playwright_sina"


class SourceTier(str, Enum):
    """数据源层级：api 层优先使用，scraper 层（Playwright）仅在 api 层全部失败时降级。"""
    API = "api"
    SCRAPER = "scraper"


@dataclass
class SourcePreference:
    """数据源偏好配置"""
    source: SourceType
    priority: int = 0  # 优先级，数字越小优先级越高
    timeout: float = 30.0  # 超时时间（秒）
    enabled: bool = True
    tier: SourceTier = SourceTier.API


# 默认数据源偏好配置
DEFAULT_PREFERENCES: Dict[DataType, List[SourcePreference]] = {
    DataType.SNAPSHOT: [
        SourcePreference(SourceType.EASTMONEY, priority=1, timeout=10),
        SourcePreference(SourceType.TENCENT, priority=2, timeout=10),
        SourcePreference(SourceType.SINA, priority=3, timeout=15),
    ],
    DataType.DAILY: [
        SourcePreference(SourceType.BAOSTOCK, priority=1, timeout=30),
        SourcePreference(SourceType.EASTMONEY, priority=2, timeout=30),
        SourcePreference(SourceType.TDX, priority=3, timeout=30),
    ],
    DataType.MINUTE: [
        SourcePreference(SourceType.EASTMONEY, priority=1, timeout=20),
        SourcePreference(SourceType.TENCENT, priority=2, timeout=20),
    ],
    DataType.FINANCIAL: [
        SourcePreference(SourceType.EASTMONEY, priority=1, timeout=30),
        SourcePreference(SourceType.SINA, priority=2, timeout=30),
    ],
    DataType.MONEY_FLOW: [
        SourcePreference(SourceType.EASTMONEY, priority=1, timeout=20),
    ],
    DataType.LHB: [
        SourcePreference(SourceType.EASTMONEY, priority=1, timeout=20),
    ],
    DataType.MARGIN: [
        SourcePreference(SourceType.EASTMONEY, priority=1, timeout=20),
    ],
    DataType.INFO: [
        SourcePreference(SourceType.EASTMONEY, priority=1, timeout=15),
        SourcePreference(SourceType.BAOSTOCK, priority=2, timeout=20),
    ],
    DataType.STOCK_LIST: [
        SourcePreference(SourceType.EASTMONEY, priority=1, timeout=30),
        SourcePreference(SourceType.BAOSTOCK, priority=2, timeout=60),
    ],
    DataType.VALUATION: [
        SourcePreference(SourceType.EASTMONEY, priority=1, timeout=20),
    ],
    DataType.INDUSTRY: [
        SourcePreference(SourceType.EASTMONEY, priority=1, timeout=20),
        SourcePreference(SourceType.BAOSTOCK, priority=2, timeout=60),
    ],
    DataType.DIVIDEND: [
        SourcePreference(SourceType.EASTMONEY, priority=1, timeout=20),
    ],
    DataType.GLOBAL_INDEX: [
        SourcePreference(SourceType.EASTMONEY, priority=1, timeout=20),
    ],
    # 新增数据类型的默认偏好（当前仅 api 层）
    DataType.CONCEPT_LIST: [
        SourcePreference(source=SourceType.EASTMONEY, priority=1, timeout=10.0, tier=SourceTier.API),
        SourcePreference(source=SourceType.SINA, priority=2, timeout=10.0, tier=SourceTier.API),
    ],
    DataType.CONCEPT_CONSTITUENTS: [
        SourcePreference(source=SourceType.EASTMONEY, priority=1, timeout=10.0, tier=SourceTier.API),
        SourcePreference(source=SourceType.SINA, priority=2, timeout=10.0, tier=SourceTier.API),
    ],
    DataType.CONCEPT_MONEY_FLOW: [
        SourcePreference(source=SourceType.EASTMONEY, priority=1, timeout=10.0, tier=SourceTier.API),
    ],
    DataType.MONEY_FLOW_STOCK: [
        SourcePreference(source=SourceType.EASTMONEY, priority=1, timeout=10.0, tier=SourceTier.API),
        SourcePreference(source=SourceType.SINA, priority=2, timeout=10.0, tier=SourceTier.API),
    ],
    DataType.EARNINGS_CALENDAR: [
        SourcePreference(source=SourceType.EASTMONEY, priority=1, timeout=10.0, tier=SourceTier.API),
    ],
    DataType.EARNINGS_PREANNOUNCE: [
        SourcePreference(source=SourceType.EASTMONEY, priority=1, timeout=10.0, tier=SourceTier.API),
    ],
    DataType.MARKET_OVERVIEW: [
        SourcePreference(source=SourceType.EASTMONEY, priority=1, timeout=10.0, tier=SourceTier.API),
        SourcePreference(source=SourceType.SINA, priority=2, timeout=10.0, tier=SourceTier.API),
    ],
    DataType.MARGIN_SUMMARY: [
        SourcePreference(source=SourceType.EASTMONEY, priority=1, timeout=10.0, tier=SourceTier.API),
        SourcePreference(source=SourceType.SINA, priority=2, timeout=10.0, tier=SourceTier.API),
    ],
}


class SmartRouter:
    """
    智能路由器

    根据数据类型和数据源健康状态动态选择最佳数据源。
    """

    def __init__(self, preferences: Optional[Dict[DataType, List[SourcePreference]]] = None):
        """
        初始化路由器

        Args:
            preferences: 数据源偏好配置
        """
        self.preferences = preferences if preferences is not None else DEFAULT_PREFERENCES.copy()
        self._source_health: Dict[SourceType, Dict[str, Any]] = {}
        self._source_stats: Dict[SourceType, Dict[str, Any]] = {}

    def get_preferred_source(self, data_type: DataType) -> Optional[SourceType]:
        """
        获取首选数据源

        Args:
            data_type: 数据类型

        Returns:
            最佳数据源
        """
        prefs = self.preferences.get(data_type, [])
        if not prefs:
            return None

        # 按优先级排序，排除不健康的数据源
        for pref in sorted(prefs, key=lambda x: x.priority):
            if not pref.enabled:
                continue

            # 检查数据源健康状态
            source_health = self._source_health.get(pref.source)
            if source_health:
                is_healthy = source_health.get("is_healthy", True)
                if not is_healthy:
                    logger.debug(f"数据源 {pref.source.value} 不健康，跳过")
                    continue

            return pref.source

        logger.warning(f"没有可用的数据源 for {data_type.value}")
        return None

    def get_tiered_sources(self, data_type: DataType) -> tuple[list[SourcePreference], list[SourcePreference]]:
        """返回分层的源列表：(api_tier_sources, scraper_tier_sources)。
        每层内部按 priority 排序。跳过 disabled 和不健康的源。
        """
        prefs = self.preferences.get(data_type, [])
        api_sources = []
        scraper_sources = []

        for pref in sorted(prefs, key=lambda p: p.priority):
            if not pref.enabled:
                continue
            health = self._source_health.get(pref.source)
            if health and not health.get("is_healthy", True):
                continue
            if pref.tier == SourceTier.SCRAPER:
                scraper_sources.append(pref)
            else:
                api_sources.append(pref)

        return api_sources, scraper_sources

    def update_source_health(
        self,
        source: SourceType,
        is_healthy: bool,
        error_msg: Optional[str] = None,
    ) -> None:
        """
        更新数据源健康状态

        Args:
            source: 数据源
            is_healthy: 是否健康
            error_msg: 错误信息
        """
        self._source_health[source] = {
            "is_healthy": is_healthy,
            "last_check": time.time(),
            "error_msg": error_msg,
        }

    def record_request(
        self,
        source: SourceType,
        data_type: DataType,
        success: bool,
        response_time: float,
    ) -> None:
        """
        记录请求统计

        Args:
            source: 数据源
            data_type: 数据类型
            success: 是否成功
            response_time: 响应时间（秒）
        """
        if source not in self._source_stats:
            self._source_stats[source] = {
                "total_requests": 0,
                "successful_requests": 0,
                "failed_requests": 0,
                "total_response_time": 0.0,
                "last_request_time": None,
            }

        stats = self._source_stats[source]
        stats["total_requests"] += 1
        if success:
            stats["successful_requests"] += 1
        else:
            stats["failed_requests"] += 1

        stats["total_response_time"] += response_time
        stats["last_request_time"] = time.time()

    def get_source_stats(self, source: Optional[SourceType] = None) -> Dict[str, Any]:
        """
        获取数据源统计

        Args:
            source: 数据源，None表示所有

        Returns:
            统计信息
        """
        if source:
            stats = self._source_stats.get(source, {})
            return self._calc_stats(source, stats)

        result = {}
        for src, stats in self._source_stats.items():
            result[src.value] = self._calc_stats(src, stats)
        return result

    def _calc_stats(self, source: SourceType, stats: Dict[str, Any]) -> Dict[str, Any]:
        """计算统计信息"""
        total = stats.get("total_requests", 0)
        success = stats.get("successful_requests", 0)

        return {
            "total_requests": total,
            "successful_requests": success,
            "failed_requests": stats.get("failed_requests", 0),
            "success_rate": success / total if total > 0 else 0,
            "avg_response_time": stats.get("total_response_time", 0) / total if total > 0 else 0,
            "last_request_time": stats.get("last_request_time"),
        }

    def get_health_status(self) -> Dict[str, Any]:
        """获取所有数据源健康状态"""
        return {
            source.value: health
            for source, health in self._source_health.items()
        }

    def set_preference(self, data_type: DataType, prefs: List[SourcePreference]) -> None:
        """设置数据源偏好"""
        self.preferences[data_type] = prefs

    def enable_source(self, source: SourceType) -> None:
        """启用数据源"""
        for prefs in self.preferences.values():
            for pref in prefs:
                if pref.source == source:
                    pref.enabled = True

    def disable_source(self, source: SourceType) -> None:
        """禁用数据源"""
        for prefs in self.preferences.values():
            for pref in prefs:
                if pref.source == source:
                    pref.enabled = False
        logger.info(f"已禁用数据源: {source.value}")


# 全局路由器
_router: Optional[SmartRouter] = None


def get_router() -> SmartRouter:
    """获取路由器实例"""
    global _router
    if _router is None:
        _router = SmartRouter()
    return _router


def set_router(router: SmartRouter) -> None:
    """设置路由器实例"""
    global _router
    _router = router


__all__ = [
    "DataType",
    "SourceType",
    "SourceTier",
    "SourcePreference",
    "SmartRouter",
    "DEFAULT_PREFERENCES",
    "get_router",
    "set_router",
]
