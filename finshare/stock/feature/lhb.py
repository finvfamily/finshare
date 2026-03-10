"""
龙虎榜数据接口
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


def get_lhb(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
) -> pd.DataFrame:
    """
    获取龙虎榜数据

    Args:
        start_date: 开始日期 (YYYYMMDD)，默认最近30天
        end_date: 结束日期 (YYYYMMDD)，默认今天

    Returns:
        DataFrame 包含以下字段:
        - fs_code: 股票代码
        - trade_date: 上榜日期
        - close_price: 收盘价
        - change_rate: 涨跌幅
        - net_buy_amount: 龙虎榜净买额
        - buy_amount: 龙虎榜买入额
        - sell_amount: 龙虎榜卖出额
        - turnover_rate: 换手率
        - reason: 上榜原因

    Example:
        >>> df = get_lhb()
        >>> print(df[['fs_code', 'trade_date', 'net_buy_amount', 'reason']].head(10))
    """
    client = _get_client()
    return client.get_lhb(start_date, end_date)


def get_lhb_detail(
    code: str,
    trade_date: Optional[str] = None,
) -> pd.DataFrame:
    """
    获取龙虎榜明细

    Args:
        code: 股票代码 (000001.SZ, 600519.SH)
        trade_date: 交易日期 (YYYYMMDD)，默认今天

    Returns:
        DataFrame 包含以下字段:
        - fs_code: 股票代码
        - trade_date: 交易日期
        - broker_name: 营业部名称
        - buy_amount: 买入金额
        - sell_amount: 卖出金额
        - net_amount: 净买额

    Example:
        >>> df = get_lhb_detail("000001.SZ")
        >>> print(df[['broker_name', 'buy_amount', 'sell_amount', 'net_amount']])
    """
    client = _get_client()
    return client.get_lhb_detail(code, trade_date)
