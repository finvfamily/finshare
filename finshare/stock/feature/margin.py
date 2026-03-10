"""
融资融券数据接口
"""

import pandas as pd
from typing import Optional
from finshare.stock.feature.client import FeatureClient


# 全局客户端
_client = None


def _get_client() -> FeatureClient:
    """获取客户端单例"""
    global _client
    if _client is None:
        _client = FeatureClient()
    return _client


def get_margin(code: Optional[str] = None) -> pd.DataFrame:
    """
    获取融资融券数据

    Args:
        code: 股票代码 (000001.SZ, 600519.SH)，不传则获取市场汇总

    Returns:
        DataFrame 包含以下字段:
        - fs_code: 股票代码
        - trade_date: 交易日期
        - rzye: 融资余额(元)
        - rqyl: 融券余量(股)
        - rzje: 融资买入额(元)
        - rqmcl: 融券卖出量(股)
        - rzrqye: 融资融券余额(元)

    Example:
        >>> df = get_margin("000001.SZ")
        >>> print(df[['trade_date', 'rzye', 'rqyl']])
    """
    client = _get_client()
    return client.get_margin(code)


def get_margin_detail(
    code: str,
    trade_date: Optional[str] = None,
) -> pd.DataFrame:
    """
    获取个股融资融券明细

    Args:
        code: 股票代码 (000001.SZ, 600519.SH)
        trade_date: 交易日期 (YYYYMMDD)，默认今天

    Returns:
        DataFrame 包含以下字段:
        - fs_code: 股票代码
        - trade_date: 交易日期
        - rzye: 融资余额(元)
        - rqyl: 融券余量(股)
        - rzrqye: 融资融券余额(元)

    Example:
        >>> df = get_margin_detail("000001.SZ")
        >>> print(df)
    """
    client = _get_client()
    return client.get_margin_detail(code, trade_date)
