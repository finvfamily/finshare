"""
财务指标数据接口
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


def get_financial_indicator(
    code: str,
    ann_date: Optional[str] = None,
) -> pd.DataFrame:
    """
    获取财务指标数据

    Args:
        code: 股票代码 (000001.SZ, 600519.SH)
        ann_date: 公告日期 (YYYYMMDD)

    Returns:
        DataFrame 包含以下字段:
        - fs_code: 股票代码
        - ann_date: 公告日期
        - report_date: 报告期
        - eps: 每股收益(元)
        - roe: 净资产收益率(%)
        - gross_margin: 毛利率(%)
        - netprofit_margin: 净利率(%)
        - current_ratio: 流动比率
        - quick_ratio: 速动比率
        - debt_to_assets: 资产负债率(%)
        - invturn: 存货周转率
        - arturn: 应收账款周转率

    Example:
        >>> df = get_financial_indicator("000001.SZ")
        >>> print(df[['fs_code', 'report_date', 'eps', 'roe', 'gross_margin']])
    """
    client = _get_client()
    return client.get_financial_indicator(code, ann_date)
