"""
资金流向数据接口
"""

import pandas as pd
from finshare.stock.feature.client import FeatureClient


# 全局客户端
_client = None


def _get_client() -> FeatureClient:
    """获取客户端单例"""
    global _client
    if _client is None:
        _client = FeatureClient()
    return _client


def get_money_flow(code: str) -> pd.DataFrame:
    """
    获取个股资金流向

    Args:
        code: 股票代码 (000001.SZ, 600519.SH)

    Returns:
        DataFrame 包含以下字段:
        - fs_code: 股票代码
        - trade_date: 交易日期
        - net_inflow_main: 主力净流入(元)
        - net_inflow_super: 超大单净流入(元)
        - net_inflow_large: 大单净流入(元)
        - net_inflow_medium: 中单净流入(元)
        - net_inflow_small: 小单净流入(元)
        - net_inflow_main_ratio: 主力净流入占比(%)
        - net_inflow_super_ratio: 超大单净流入占比(%)
        - net_inflow_large_ratio: 大单净流入占比(%)
        - net_inflow_medium_ratio: 中单净流入占比(%)
        - net_inflow_small_ratio: 小单净流入占比(%)

    Example:
        >>> df = get_money_flow("000001.SZ")
        >>> print(df[['fs_code', 'net_inflow_main', 'net_inflow_main_ratio']])
    """
    client = _get_client()
    return client.get_money_flow(code)


def get_money_flow_industry() -> pd.DataFrame:
    """
    获取行业资金流向

    Returns:
        DataFrame 包含以下字段:
        - industry: 行业名称
        - net_inflow: 净流入(元)
        - net_inflow_ratio: 净流入占比(%)
        - change_rate: 涨跌幅(%)

    Example:
        >>> df = get_money_flow_industry()
        >>> print(df[['industry', 'change_rate']].head(10))
    """
    client = _get_client()
    return client.get_money_flow_industry()
