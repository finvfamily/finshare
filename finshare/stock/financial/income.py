"""
利润表数据接口
"""

import pandas as pd
from typing import Optional
from finshare.stock.financial.client import FinancialClient


# 全局客户端
_client = None


def _get_client() -> FinancialClient:
    """获取财务客户端单例"""
    global _client
    if _client is None:
        _client = FinancialClient()
    return _client


def get_income(
    code: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
) -> pd.DataFrame:
    """
    获取利润表数据

    Args:
        code: 股票代码 (000001.SZ, 600519.SH)
        start_date: 开始日期 (YYYYMMDD)
        end_date: 结束日期 (YYYYMMDD)

    Returns:
        DataFrame 包含以下字段:
        - fs_code: 股票代码
        - ann_date: 公告日期
        - report_date: 报告期
        - revenue: 营业收入
        - revenue_yoy: 营业收入同比(%)
        - net_profit: 净利润
        - net_profit_yoy: 净利润同比(%)
        - gross_margin: 毛利率(%)
        - roe: 净资产收益率(%)

    Example:
        >>> df = get_income("000001.SZ")
        >>> print(df.head())
    """
    client = _get_client()
    return client.get_income(code, start_date, end_date)
