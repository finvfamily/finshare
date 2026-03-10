"""
分红送股数据接口
"""

import pandas as pd
from finshare.stock.financial.client import FinancialClient


# 全局客户端
_client = None


def _get_client() -> FinancialClient:
    """获取财务客户端单例"""
    global _client
    if _client is None:
        _client = FinancialClient()
    return _client


def get_dividend(code: str) -> pd.DataFrame:
    """
    获取分红送股数据

    Args:
        code: 股票代码 (000001.SZ, 600519.SH)

    Returns:
        DataFrame 包含以下字段:
        - fs_code: 股票代码
        - ann_date: 公告日期
        - divident_date: 分红日期
        - cash_div: 现金分红(元/股)
        - stock_div: 送股(股/10股)
        - stock_ratio: 送股比例
        - bonus_ratio: 分红比例

    Example:
        >>> df = get_dividend("000001.SZ")
        >>> print(df[['ann_date', 'cash_div', 'stock_div']])
    """
    client = _get_client()
    return client.get_dividend(code)
