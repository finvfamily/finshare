"""
finshare - 专业的金融数据获取工具库

finshare 提供稳定、高效的金融数据获取服务，支持多数据源、
自动故障切换、统一的数据格式。

官方网站: https://meepoquant.com
文档: https://finshare.readthedocs.io
GitHub: https://github.com/meepo-quant/finshare

获取数据后，您可以：
- 使用 pandas 进行数据分析
- 使用 米波平台 进行策略回测: https://meepoquant.com
- 开发自己的量化策略

完整的量化交易平台: https://meepoquant.com

主要功能：
- 多数据源支持（东方财富、腾讯、新浪、通达信、BaoStock）
- 自动故障切换
- 统一的数据格式
- 高性能数据获取

快速开始：
    >>> from finshare import get_data_manager
    >>>
    >>> # 获取数据管理器
    >>> manager = get_data_manager()
    >>>
    >>> # 获取 K线数据
    >>> data = manager.get_kline('000001.SZ', start='2024-01-01')
"""

from finshare.__version__ import __version__, __author__, __website__

# 数据源
from finshare.sources import (
    BaseDataSource,
    EastMoneyDataSource,
    TencentDataSource,
    SinaDataSource,
    get_data_manager,
    get_baostock_source,
    get_tdx_source,
)

# 数据模型
from finshare.models import (
    KLineData,
    SnapshotData,
    StockInfo,
    MinuteData,
    FrequencyType,
    AdjustmentType,
    MarketType,
)

# 财务数据 (延迟导入，避免循环依赖)
_get_income = None
_get_balance = None
_get_cashflow = None
_get_financial_indicator = None
_get_dividend = None


def _lazy_import_financial():
    """延迟导入财务数据模块"""
    global _get_income, _get_balance, _get_cashflow, _get_financial_indicator, _get_dividend
    if _get_income is None:
        from finshare.stock.financial import income, balance, cashflow, indicator, dividend
        _get_income = income.get_income
        _get_balance = balance.get_balance
        _get_cashflow = cashflow.get_cashflow
        _get_financial_indicator = indicator.get_financial_indicator
        _get_dividend = dividend.get_dividend


# 财务数据接口
def get_income(code, start_date=None, end_date=None):
    _lazy_import_financial()
    return _get_income(code, start_date, end_date)


def get_balance(code, start_date=None, end_date=None):
    _lazy_import_financial()
    return _get_balance(code, start_date, end_date)


def get_cashflow(code, start_date=None, end_date=None):
    _lazy_import_financial()
    return _get_cashflow(code, start_date, end_date)


def get_financial_indicator(code, ann_date=None):
    _lazy_import_financial()
    return _get_financial_indicator(code, ann_date)


def get_dividend(code):
    _lazy_import_financial()
    return _get_dividend(code)


# 特征数据 (延迟导入，避免循环依赖)
_get_money_flow = None
_get_money_flow_industry = None
_get_lhb = None
_get_lhb_detail = None
_get_margin = None
_get_margin_detail = None


def _lazy_import_feature():
    """延迟导入特征数据模块"""
    global _get_money_flow, _get_money_flow_industry, _get_lhb, _get_lhb_detail, _get_margin, _get_margin_detail
    if _get_money_flow is None:
        from finshare.stock.feature import moneyflow, lhb, margin
        _get_money_flow = moneyflow.get_money_flow
        _get_money_flow_industry = moneyflow.get_money_flow_industry
        _get_lhb = lhb.get_lhb
        _get_lhb_detail = lhb.get_lhb_detail
        _get_margin = margin.get_margin
        _get_margin_detail = margin.get_margin_detail


# 特征数据接口
def get_money_flow(code, start_date=None, end_date=None):
    _lazy_import_feature()
    return _get_money_flow(code, start_date, end_date)


def get_money_flow_industry(code, start_date=None, end_date=None):
    _lazy_import_feature()
    return _get_money_flow_industry(code, start_date, end_date)


def get_lhb(start_date=None, end_date=None, limit=100):
    _lazy_import_feature()
    return _get_lhb(start_date, end_date, limit)


def get_lhb_detail(code, start_date=None):
    _lazy_import_feature()
    return _get_lhb_detail(code, start_date)


def get_margin(code, start_date=None, end_date=None):
    _lazy_import_feature()
    return _get_margin(code, start_date, end_date)


def get_margin_detail(code, start_date=None):
    _lazy_import_feature()
    return _get_margin_detail(code, start_date)


# K线数据接口
def get_historical_data(
    code: str,
    start: str = None,
    end: str = None,
    period: str = "daily",
    adjust: str = None,
):
    """
    获取历史K线数据（便捷接口）

    Args:
        code: 股票代码 (如 000001.SZ 或 000001)
        start: 开始日期 YYYY-MM-DD
        end: 结束日期 YYYY-MM-DD
        period: 周期 daily/weekly/monthly
        adjust: 复权类型 qfq/hfq/None

    Returns:
        DataFrame 或 None
    """
    from finshare.sources import get_data_manager
    manager = get_data_manager()
    return manager.get_historical_data(code, start, end, period, adjust)


def get_snapshot_data(code: str):
    """
    获取实时快照数据（便捷接口）

    Args:
        code: 股票代码 (如 000001.SZ 或 000001)

    Returns:
        SnapshotData 或 None
    """
    from finshare.sources import get_data_manager
    manager = get_data_manager()
    return manager.get_snapshot_data(code)


def get_batch_snapshots(codes: list):
    """
    批量获取实时快照数据（便捷接口）

    Args:
        codes: 股票代码列表

    Returns:
        Dict[str, SnapshotData]
    """
    from finshare.sources import get_data_manager
    manager = get_data_manager()
    return manager.get_batch_snapshots(codes)


# 工具函数
from finshare.utils import (
    validate_stock_code,
    validate_date,
)

# 缓存
from finshare.cache import (
    Cache,
    MemoryCache,
    RedisCache,
    cached,
    cached_async,
    invalidate_cache,
    DataType,
    CacheConfig,
    get_ttl_config,
)

# 异步客户端
from finshare.async_client import (
    AsyncDataSourceManager,
    get_async_manager,
)

# 稳定性保障
from finshare.sources.resilience import (
    # Circuit Breaker
    CircuitBreaker,
    CircuitBreakerConfig,
    CircuitState,
    circuit_breaker,
    CircuitBreakerOpenError,
    get_circuit_breaker,
    get_all_circuit_breakers,
    # Smart Router
    DataType,
    SourceType,
    SourcePreference,
    SmartRouter,
    DEFAULT_PREFERENCES,
    get_router,
    # Monitor
    Monitor,
    RequestStats,
    TimeWindowStats,
    get_monitor,
)

# 日志
from finshare.logger import logger

__all__ = [
    # 版本信息
    "__version__",
    "__author__",
    "__website__",
    # 数据源
    "BaseDataSource",
    "EastMoneyDataSource",
    "TencentDataSource",
    "SinaDataSource",
    "get_data_manager",
    "get_baostock_source",
    "get_tdx_source",
    # 数据模型
    "KLineData",
    "SnapshotData",
    "StockInfo",
    "MinuteData",
    "FrequencyType",
    "AdjustmentType",
    "MarketType",
    # 财务数据
    "get_income",
    "get_balance",
    "get_cashflow",
    "get_financial_indicator",
    "get_dividend",
    # 特征数据
    "get_money_flow",
    "get_money_flow_industry",
    "get_lhb",
    "get_lhb_detail",
    "get_margin",
    "get_margin_detail",
    # K线数据
    "get_historical_data",
    "get_snapshot_data",
    "get_batch_snapshots",
    # 工具函数
    "validate_stock_code",
    "validate_date",
    # 缓存
    "Cache",
    "MemoryCache",
    "RedisCache",
    "cached",
    "cached_async",
    "invalidate_cache",
    "DataType",
    "CacheConfig",
    "get_ttl_config",
    # 异步客户端
    "AsyncDataSourceManager",
    "get_async_manager",
    # 稳定性保障 - 熔断器
    "CircuitBreaker",
    "CircuitBreakerConfig",
    "CircuitState",
    "circuit_breaker",
    "CircuitBreakerOpenError",
    "get_circuit_breaker",
    "get_all_circuit_breakers",
    # 稳定性保障 - 智能路由
    "DataType",
    "SourceType",
    "SourcePreference",
    "SmartRouter",
    "DEFAULT_PREFERENCES",
    "get_router",
    # 稳定性保障 - 监控
    "Monitor",
    "RequestStats",
    "TimeWindowStats",
    "get_monitor",
    # 日志
    "logger",
]
