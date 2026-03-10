"""
现金流量表数据接口
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


def get_cashflow(
    code: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
) -> pd.DataFrame:
    """
    获取现金流量表数据

    Args:
        code: 股票代码 (000001.SZ, 600519.SH)
        start_date: 开始日期 (YYYYMMDD)
        end_date: 结束日期 (YYYYMMDD)

    Returns:
        DataFrame 包含以下字段:
        - fs_code: 股票代码
        - ann_date: 公告日期
        - report_date: 报告期
        - operate_cashflow: 经营活动现金流
        - invest_cashflow: 投资活动现金流
        - finance_cashflow: 筹资活动现金流

    Example:
        >>> df = get_cashflow("000001.SZ")
    """
    client = _get_client()
    return client.get_cashflow(code, start_date, end_date)
