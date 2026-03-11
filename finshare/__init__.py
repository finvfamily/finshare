"""
finshare - 专业的金融数据获取工具库

finshare 提供稳定、高效的金融数据获取服务，支持多数据源、
自动故障切换、统一的数据格式。

官方网站: https://meepoquant.com
文档: https://finvfamily.github.io/finshare/
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
def get_money_flow(code: str):
    """获取资金流向

    Args:
        code: 股票代码 (如 000001.SZ)

    Returns:
        DataFrame
    """
    _lazy_import_feature()
    return _get_money_flow(code)


def get_money_flow_industry():
    """获取行业资金流向

    Returns:
        DataFrame
    """
    _lazy_import_feature()
    return _get_money_flow_industry()


def get_lhb(start_date=None, end_date=None):
    """获取龙虎榜数据

    Args:
        start_date: 开始日期 (YYYYMMDD)，默认最近30天
        end_date: 结束日期 (YYYYMMDD)，默认今天

    Returns:
        DataFrame
    """
    _lazy_import_feature()
    return _get_lhb(start_date, end_date)


def get_lhb_detail(code: str, trade_date=None):
    """获取龙虎榜明细

    Args:
        code: 股票代码 (如 000001.SZ)
        trade_date: 交易日期 (YYYYMMDD)，默认今天

    Returns:
        DataFrame
    """
    _lazy_import_feature()
    return _get_lhb_detail(code, trade_date)


def get_margin(code: str = None):
    """获取融资融券数据

    Args:
        code: 股票代码 (如 000001.SZ)，不传则获取市场汇总

    Returns:
        DataFrame
    """
    _lazy_import_feature()
    return _get_margin(code)


def get_margin_detail(code: str, trade_date=None):
    """获取融资融券明细

    Args:
        code: 股票代码 (如 000001.SZ)
        trade_date: 交易日期 (YYYYMMDD)，默认今天

    Returns:
        DataFrame
    """
    _lazy_import_feature()
    return _get_margin_detail(code, trade_date)


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


# 期货数据 (延迟导入，避免循环依赖)
_get_future_kline = None
_get_future_snapshot = None
_get_batch_future_snapshots = None


def _lazy_import_future():
    """延迟导入期货数据模块"""
    global _get_future_kline, _get_future_snapshot, _get_batch_future_snapshots
    if _get_future_kline is None:
        from finshare.stock.future import get_future_kline, get_future_snapshot, get_batch_future_snapshots
        _get_future_kline = get_future_kline
        _get_future_snapshot = get_future_snapshot
        _get_batch_future_snapshots = get_batch_future_snapshots


def get_future_kline(
    code: str,
    start_date: str = None,
    end_date: str = None,
    adjustment: str = "none",
):
    """
    获取期货历史K线数据

    Args:
        code: 期货合约代码 (如 IF2409, CU2409, RB2409)
              也支持简写: IF0 (沪深300股指当月连续)
        start_date: 开始日期 (YYYY-MM-DD)
        end_date: 结束日期 (YYYY-MM-DD)
        adjustment: 复权类型 (期货不支持，默认none)

    Returns:
        List[HistoricalData] 历史K线数据列表

    Examples:
        >>> import finshare as fs
        >>> data = fs.get_future_kline('IF2409', '2024-01-01', '2024-01-31')
    """
    _lazy_import_future()
    return _get_future_kline(code, start_date, end_date, adjustment)


def get_future_snapshot(code: str):
    """
    获取期货实时快照数据

    Args:
        code: 期货合约代码 (如 IF2409, CU2409)

    Returns:
        FutureSnapshotData 实时快照数据

    Examples:
        >>> import finshare as fs
        >>> snapshot = fs.get_future_snapshot('IF2409')
        >>> print(f"最新价: {snapshot.last_price}")
    """
    _lazy_import_future()
    return _get_future_snapshot(code)


def get_batch_future_snapshots(codes: list):
    """
    批量获取期货实时快照

    Args:
        codes: 期货合约代码列表

    Returns:
        Dict[str, FutureSnapshotData]

    Examples:
        >>> import finshare as fs
        >>> snapshots = fs.get_batch_future_snapshots(['IF2409', 'CU2409'])
    """
    _lazy_import_future()
    return _get_batch_future_snapshots(codes)


# 基金数据 (延迟导入，避免循环依赖)
_get_fund_nav = None
_get_fund_info = None
_get_fund_list = None


def _lazy_import_fund():
    """延迟导入基金数据模块"""
    global _get_fund_nav, _get_fund_info, _get_fund_list
    if _get_fund_nav is None:
        from finshare.stock.fund import get_fund_nav, get_fund_info, get_fund_list
        _get_fund_nav = get_fund_nav
        _get_fund_info = get_fund_info
        _get_fund_list = get_fund_list


def get_fund_nav(
    code: str,
    start_date: str = None,
    end_date: str = None,
):
    """
    获取基金净值数据

    Args:
        code: 基金代码 (如 161039, 000001)
        start_date: 开始日期 (YYYY-MM-DD)
        end_date: 结束日期 (YYYY-MM-DD)

    Returns:
        List[FundData] 基金净值数据列表

    Examples:
        >>> import finshare as fs
        >>> data = fs.get_fund_nav('161039', '2024-01-01', '2024-01-31')
        >>> for item in data:
        >>>     print(f"{item.nav_date}: nav={item.nav}")
    """
    _lazy_import_fund()
    return _get_fund_nav(code, start_date, end_date)


def get_fund_info(code: str):
    """
    获取基金基本信息

    Args:
        code: 基金代码

    Returns:
        基金信息字典

    Examples:
        >>> import finshare as fs
        >>> info = fs.get_fund_info('161039')
    """
    _lazy_import_fund()
    return _get_fund_info(code)


def get_fund_list(market: str = "all"):
    """
    获取基金列表

    Args:
        market: 市场类型 (all: 全部, sh: 上海, sz: 深圳)

    Returns:
        基金列表

    Examples:
        >>> import finshare as fs
        >>> funds = fs.get_fund_list()
    """
    _lazy_import_fund()
    return _get_fund_list(market)


# 证券列表 (延迟导入)
_get_stock_list = None
_get_etf_list = None
_get_lof_list = None
_get_future_list = None


def _lazy_import_list():
    """延迟导入列表模块"""
    global _get_stock_list, _get_etf_list, _get_lof_list, _get_future_list
    if _get_stock_list is None:
        from finshare.stock.security_list import get_stock_list, get_etf_list, get_lof_list, get_future_list
        _get_stock_list = get_stock_list
        _get_etf_list = get_etf_list
        _get_lof_list = get_lof_list
        _get_future_list = get_future_list


def get_stock_list(market: str = "all"):
    """
    获取A股股票列表

    Args:
        market: 市场类型 (all: 全部, sh: 上海, sz: 深圳)

    Returns:
        List[Dict] 股票列表

    Examples:
        >>> import finshare as fs
        >>> stocks = fs.get_stock_list()
        >>> print(f"共有 {len(stocks)} 只股票")
    """
    _lazy_import_list()
    return _get_stock_list(market)


def get_etf_list():
    """
    获取ETF基金列表

    Returns:
        List[Dict] ETF列表

    Examples:
        >>> import finshare as fs
        >>> etfs = fs.get_etf_list()
        >>> print(f"共有 {len(etfs)} 只ETF")
    """
    _lazy_import_list()
    return _get_etf_list()


def get_lof_list():
    """
    获取LOF基金列表

    Returns:
        List[Dict] LOF列表

    Examples:
        >>> import finshare as fs
        >>> lofs = fs.get_lof_list()
        >>> print(f"共有 {len(lofs)} 只LOF")
    """
    _lazy_import_list()
    return _get_lof_list()


def get_future_list():
    """
    获取期货列表

    Returns:
        List[Dict] 期货列表

    Examples:
        >>> import finshare as fs
        >>> futures = fs.get_future_list()
        >>> print(f"共有 {len(futures)} 个期货合约")
    """
    _lazy_import_list()
    return _get_future_list()


# 工具函数
from finshare.utils import (  # noqa: E402
    validate_stock_code,
    validate_date,
)

# 缓存
from finshare.cache import (  # noqa: E402
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
from finshare.async_client import (  # noqa: E402
    AsyncDataSourceManager,
    get_async_manager,
)

# 稳定性保障
from finshare.sources.resilience import (  # noqa: E402
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
from finshare.logger import logger  # noqa: E402

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
    # 期货数据模型
    "FutureData",
    "FutureSnapshotData",
    "FutureExchange",
    # 基金数据模型
    "FundData",
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
    # 期货数据
    "get_future_kline",
    "get_future_snapshot",
    "get_batch_future_snapshots",
    # 基金数据
    "get_fund_nav",
    "get_fund_info",
    "get_fund_list",
    # 证券列表
    "get_stock_list",
    "get_etf_list",
    "get_lof_list",
    "get_future_list",
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
