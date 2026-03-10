"""
资产负债表数据接口
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


def get_balance(
    code: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
) -> pd.DataFrame:
    """
    获取资产负债表数据

    Args:
        code: 股票代码 (000001.SZ, 600519.SH)
        start_date: 开始日期 (YYYYMMDD)
        end_date: 结束日期 (YYYYMMDD)

    Returns:
        DataFrame 包含以下字段:
        - fs_code: 股票代码
        - ann_date: 公告日期
        - report_date: 报告期
        - total_assets: 总资产
        - total_liab: 总负债
        - total_equity: 股东权益
        - current_assets: 流动资产
        - current_liab: 流动负债

    Example:
        >>> df = get_balance("000001.SZ")
    """
    client = _get_client()
    return client.get_balance(code, start_date, end_date)
